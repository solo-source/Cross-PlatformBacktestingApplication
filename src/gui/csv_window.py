# src/gui/csv_window.py

import pandas as pd
from PySide6.QtWidgets import QPushButton, QFileDialog, QMessageBox
from src.data.loader import DataLoader
from src.backtester.engine import BacktestEngine
from src.gui.base_backtest_window import BaseBacktestWindow

# Import the strategy class to check for MultiTimeframeSma
from src.backtester.strategies import MultiTimeframeSma

from backtrader import feeds


class CsvBacktestWindow(BaseBacktestWindow):
    """
    Window for “Load CSV” data feed. Allows browsing for a CSV,
    loads it into Backtrader as a PandasData feed, and stores row count.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.csv_feed_path = None

    def add_data_controls(self):
        # Add “Browse CSV” button to the left panel
        self.browse_button = QPushButton("Browse CSV File...", self)
        self.browse_button.clicked.connect(self.on_browse_csv)
        self.left_layout.addRow(self.browse_button)

    def on_browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            feed, row_count = DataLoader.from_csv(path)
            self.csv_feed_path = path
            self.data_rows = row_count
            # Preload engine so run_backtest() sees something
            self.engine = BacktestEngine()
            # Note: do NOT attach here; we attach in run_backtest()
            QMessageBox.information(
                self,
                "CSV Loaded",
                f"Loaded CSV: {path}\n{row_count} bars available."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error loading CSV", str(e))

    def attach_data_feed_to_engine(self):
        """
        Called by run_backtest():
          * If the chosen strategy is MultiTimeframeSma, add two feeds:
              1) A daily PandasData feed
              2) A weekly PandasData feed (resampled from the same CSV)
          * Otherwise, just add the single daily feed.
        """

        # Always read the CSV into a DataFrame first
        df = pd.read_csv(
            self.csv_feed_path,
            parse_dates=['Date'],
            dtype={'Open': float, 'High': float, 'Low': float, 'Close': float, 'Volume': int}
        )
        df.rename(columns={'Date': 'datetime'}, inplace=True)
        df.sort_values('datetime', inplace=True)
        df['openinterest'] = 0

        # Build the primary (daily) feed
        daily_feed = feeds.PandasData(
            dataname=df,
            datetime='datetime',
            open='Open',
            high='High',
            low='Low',
            close='Close',
            volume='Volume',
            openinterest='openinterest'
        )
        self.engine.add_data(daily_feed)

        # Now check if the selected strategy is MultiTimeframeSma
        strat_cls, _ = self.strategy_selector.get_strategy()
        if strat_cls is MultiTimeframeSma:
            # Resample to weekly (or your chosen higher timeframe)
            #   Note: 'W-FRI' means weekly period ending on Friday.
            df_weekly = df.resample('W-FRI', on='datetime').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum',
            })
            # Drop any rows with NaN (e.g. if a week had no data)
            df_weekly.dropna(inplace=True)
            df_weekly['openinterest'] = 0
            df_weekly.reset_index(inplace=True)  # Make 'datetime' a column again

            weekly_feed = feeds.PandasData(
                dataname=df_weekly,
                datetime='datetime',
                open='Open',
                high='High',
                low='Low',
                close='Close',
                volume='Volume',
                openinterest='openinterest'
            )
            self.engine.add_data(weekly_feed)

        # If the strategy is not MultiTimeframeSma, we already added only the daily_feed.
