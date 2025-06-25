# # src/gui/csv_window.py
#
# import pandas as pd
# from PySide6.QtWidgets import QPushButton, QFileDialog, QMessageBox
# from src.data.loader import DataLoader
# from src.backtester.engine import BacktestEngine
# from src.gui.base_backtest_window import BaseBacktestWindow
# from src.backtester.strategies import MultiTimeframeSma
# from backtrader import feeds
#
# class CsvBacktestWindow(BaseBacktestWindow):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.csv_feed_path = None
#         self.current_strat_cls = None
#
#     def add_data_controls(self):
#         btn = QPushButton("Browse CSV File...", self)
#         btn.clicked.connect(self.on_browse_csv)
#         self.left_layout.addRow(btn)
#
#     def on_browse_csv(self):
#         path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
#         if not path:
#             return
#         try:
#             _, row_count = DataLoader.from_csv(path)
#             self.csv_feed_path = path
#             self.data_rows = row_count
#             self.engine = BacktestEngine()
#             QMessageBox.information(self, "CSV Loaded", f"Loaded CSV: {path}\n{row_count} bars available.")
#         except Exception as e:
#             QMessageBox.critical(self, "Error loading CSV", str(e))
#
#     def attach_data_feed_to_engine(self):
#         df = pd.read_csv(
#             self.csv_feed_path,
#             parse_dates=['Date'],
#             dtype={'Open': float, 'High': float, 'Low': float, 'Close': float, 'Volume': int}
#         )
#         df.rename(columns={'Date': 'datetime'}, inplace=True)
#         df.sort_values('datetime', inplace=True)
#         df['openinterest'] = 0
#
#         # Daily feed
#         daily = feeds.PandasData(dataname=df, datetime='datetime', open='Open', high='High', low='Low', close='Close', volume='Volume', openinterest='openinterest')
#         self.engine.cerebro.adddata(daily)
#
#         # Weekly if strategy requires
#         if self.current_strat_cls is MultiTimeframeSma:
#             df_w = df.resample('W-FRI', on='datetime').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
#             df_w['openinterest'] = 0
#             df_w.reset_index(inplace=True)
#             weekly = feeds.PandasData(dataname=df_w, datetime='datetime', open='Open', high='High', low='Low', close='Close', volume='Volume', openinterest='openinterest')
#             self.engine.cerebro.adddata(weekly)
#
#     def get_datafeed(self):
#         if not self.csv_feed_path:
#             raise RuntimeError("No CSV loaded - please browse first.")
#
#         # fresh engine
#         self.engine = BacktestEngine()
#         strat_cls, _ = self.strategy_selector.get_strategy()
#         self.current_strat_cls = strat_cls
#
#         # attach feeds
#         self.attach_data_feed_to_engine()
#         all_feeds = list(self.engine.cerebro.datas)
#         print(f"[DEBUG] CsvBacktestWindow: attach strategy={self.current_strat_cls.__name__}, feeds count={len(all_feeds)}")
#         return all_feeds



# src/gui/csv_window.py

import pandas as pd
import backtrader as bt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem
from src.backtester.engine import BacktestEngine
from src.utils.logger import logger

class CsvBacktestWindow(QWidget):
    """
    Simplified CSV loader and preview for backtesting data.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.csv_path = None
        self.engine = None
        self.data_rows = 0
        self.df = pd.DataFrame()

        layout = QVBoxLayout(self)
        self.load_btn = QPushButton("Browse CSV File...")
        self.load_btn.clicked.connect(self.load_csv)
        layout.addWidget(self.load_btn)

        self.table = QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(["Date","Open","High","Low","Close","Volume"])
        layout.addWidget(self.table)

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if not path: return
        try:
            df = pd.read_csv(path, parse_dates=["Date"] )
            df = df.sort_values("Date")[ ["Date","Open","High","Low","Close","Volume"] ]
            self.df = df
            self.data_rows = len(df)
            self._refresh_table()
            self.engine = BacktestEngine()
            QMessageBox.information(self, "Loaded", f"CSV loaded: {self.data_rows} rows.")
        except Exception as e:
            logger.exception(e)
            QMessageBox.critical(self, "Error", str(e))

    def _refresh_table(self):
        sub = self.df.tail(100)
        self.table.setRowCount(len(sub))
        for i, (_, row) in enumerate(sub.iterrows()):
            for j, col in enumerate(["Date","Open","High","Low","Close","Volume"]):
                val = row[col]
                txt = "" if pd.isna(val) else (val.strftime("%Y-%m-%d %H:%M") if col=="Date" else f"{val}")
                self.table.setItem(i, j, QTableWidgetItem(txt))

    def get_datafeed(self):
        """Return list of bt.feeds.PandasData created from loaded CSV"""
        if self.data_rows == 0:
            raise RuntimeError("No CSV loaded - please browse first.")
        df = self.df.copy()
        df.rename(columns={"Date":"datetime"}, inplace=True)
        df.set_index("datetime", inplace=True)
        df["openinterest"] = 0
        feed = bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open="Open", high="High", low="Low",
            close="Close", volume="Volume", openinterest="openinterest"
        )
        return [feed]
