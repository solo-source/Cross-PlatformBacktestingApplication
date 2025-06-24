# src/gui/rest_window.py

from PySide6.QtWidgets import QPushButton, QFileDialog, QMessageBox
from src.data.loader import DataLoader
from src.data.stream import RestStreamer
from src.backtester.engine import BacktestEngine
from src.gui.base_backtest_window import BaseBacktestWindow
from src.utils.logger import logger
import pandas as pd


class RestBacktestWindow(BaseBacktestWindow):
    """
    Window for REST‐based data feed. User supplies a text file containing a REST URL.
    We poll the URL once on “Load Data,” convert JSON→DataFrame→PandasData feed,
    and backtest that. (Live streaming could be added later.)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rest_url = None
        self.rest_streamer = None
        self.rest_data = None  # will hold a Pandas DataFrame or similar

    def add_data_controls(self):
        self.load_button = QPushButton("Load REST URL File...", self)
        self.load_button.clicked.connect(self.on_load_rest_url)
        self.left_layout.addRow(self.load_button)

    def on_load_rest_url(self):
        # We ask user to pick a .txt that contains the URL string
        path, _ = QFileDialog.getOpenFileName(
            self, "Select REST URL File", "", "Text Files (*.txt)"
        )
        if not path:
            return

        try:
            with open(path) as f:
                self.rest_url = f.read().strip()

            # Immediately pull data once for backtest (assuming JSON OHLCV)
            # For demonstration, we pretend the JSON returns exactly
            # [{"Date":"YYYY-MM-DD", "Open":..., "High":..., ...}, ...]
            import requests
            resp = requests.get(self.rest_url, timeout=5)
            resp.raise_for_status()
            data_json = resp.json()

            # Convert to Pandas DataFrame, then back to PandasData feed
            import pandas as pd
            df = pd.DataFrame(data_json)
            # Expected columns: Date,Open,High,Low,Close,Volume
            df["Date"] = pd.to_datetime(df["Date"])
            df.sort_values("Date", inplace=True)
            df["openinterest"] = 0

            # Save DataFrame and row count; actual feed created in attach_data_feed_to_engine
            self.rest_data = df
            self.data_rows = len(df)

            # Pre-initialize engine
            self.engine = BacktestEngine()
            QMessageBox.information(
                self,
                "REST Data Loaded",
                f"REST data fetched. {self.data_rows} bars available."
            )

        except Exception as e:
            logger.exception("Failed to load REST data")
            QMessageBox.critical(self, "Error Loading REST Data", str(e))

    def attach_data_feed_to_engine(self):
        from backtrader import feeds
        from src.backtester.strategies import MultiTimeframeSma

        # Convert JSON‐fetched self.rest_data into a DataFrame
        df = self.rest_data.copy()
        df.rename(columns={'Date':'datetime'}, inplace=True)
        df.sort_values('datetime', inplace=True)
        df['openinterest'] = 0

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

        strat_cls, _ = self.strategy_selector.get_strategy()
        if strat_cls is MultiTimeframeSma:
            # Resample to weekly
            df_weekly = df.resample('W-FRI', on='datetime').agg({
                'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'
            }).dropna()
            df_weekly['openinterest'] = 0
            df_weekly.reset_index(inplace=True)
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
