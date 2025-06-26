# # src/gui/ws_window.py
#
# import sys
# import pandas as pd
# import yfinance as yf
# import backtrader as bt
# from PySide6.QtCore import Qt, QTimer
# from PySide6.QtWidgets import (
#     QWidget, QHBoxLayout, QVBoxLayout,
#     QPushButton, QFileDialog, QMessageBox,
#     QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QSpinBox
# )
# from src.backtester.engine import BacktestEngine
# from src.utils.logger import logger
#
# class WsBacktestWindow(QWidget):
#     """
#     Simplified window for live CSV or yfinance feed preview.
#     Inherits only data loading; backtest run handled by MainWindow.
#     """
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.live_df = pd.DataFrame(columns=["Date","Open","High","Low","Close","Volume"])
#         self.poll_timer = None
#         self.ticker = "SPY"
#         self.interval_min = 1
#         self.data_rows = 0
#         self.engine = None
#
#         layout = QVBoxLayout(self)
#         ctrl = QHBoxLayout()
#         layout.addLayout(ctrl)
#
#         ctrl.addWidget(QLabel("Ticker:"))
#         self.ticker_input = QLineEdit(self.ticker)
#         ctrl.addWidget(self.ticker_input)
#
#         ctrl.addWidget(QLabel("Interval (min):"))
#         self.interval_input = QSpinBox()
#         self.interval_input.setRange(1,60)
#         self.interval_input.setValue(self.interval_min)
#         ctrl.addWidget(self.interval_input)
#
#         self.live_btn = QPushButton("Start Live Feed")
#         self.live_btn.clicked.connect(self.on_toggle_live)
#         ctrl.addWidget(self.live_btn)
#
#         self.browse_btn = QPushButton("Browse CSV")
#         self.browse_btn.clicked.connect(self.on_browse_csv)
#         ctrl.addWidget(self.browse_btn)
#
#         self.rowcount = QLabel("Rows: 0")
#         ctrl.addWidget(self.rowcount)
#
#         self.table = QTableWidget(0,6)
#         self.table.setHorizontalHeaderLabels(["Date","Open","High","Low","Close","Volume"])
#         layout.addWidget(self.table)
#
#     def on_toggle_live(self):
#         if self.poll_timer and self.poll_timer.isActive():
#             self.poll_timer.stop()
#             self.poll_timer = None
#             self.live_btn.setText("Start Live Feed")
#             return
#         self.ticker = self.ticker_input.text().strip().upper()
#         if not self.ticker:
#             QMessageBox.warning(self, "Input Error", "Enter a valid ticker.")
#             return
#         self.live_df = self.live_df.iloc[0:0]
#         self.data_rows = 0
#         self.rowcount.setText("Rows: 0")
#         self._refresh_table()
#         self.poll_timer = QTimer(self)
#         self.poll_timer.timeout.connect(self.fetch_live_data)
#         self.fetch_live_data()
#         self.poll_timer.start(self.interval_input.value()*60*1000)
#         self.live_btn.setText("Stop Live Feed")
#
#     def fetch_live_data(self):
#         try:
#             df = yf.download(self.ticker, period="1d", interval=f"{self.interval_input.value()}m", progress=False, prepost=False, auto_adjust=False)
#             print(f"Fetched {len(df)} rows from yfinance for {self.ticker}")
#             if df.empty: return
#             df = df.reset_index()[["Datetime","Open","High","Low","Close","Volume"]]
#             df.rename(columns={"Datetime":"Date"}, inplace=True)
#             combined = pd.concat([self.live_df, df]).drop_duplicates(subset=["Date"]).sort_values("Date")
#             self.live_df = combined
#             self.data_rows = len(combined)
#             self.rowcount.setText(f"Rows: {self.data_rows}")
#             self._refresh_table()
#         except Exception as e:
#             logger.exception(e)
#
#     def on_browse_csv(self):
#         if self.poll_timer and self.poll_timer.isActive():
#             self.poll_timer.stop()
#             self.poll_timer = None
#             self.live_btn.setText("Start Live Feed")
#         path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
#         if not path: return
#         try:
#             df = pd.read_csv(path, parse_dates=["Date"] )
#             df = df.sort_values("Date")[ ["Date","Open","High","Low","Close","Volume"] ]
#             self.live_df = df
#             self.data_rows = len(df)
#             self.rowcount.setText(f"Rows: {self.data_rows}")
#             self._refresh_table()
#             self.engine = BacktestEngine()
#             QMessageBox.information(self, "Loaded", f"CSV loaded: {self.data_rows} rows.")
#         except Exception as e:
#             logger.exception(e)
#             QMessageBox.critical(self, "Error", str(e))
#
#     def _refresh_table(self):
#         sub = self.live_df.tail(100)
#         self.table.setRowCount(len(sub))
#         for i, (_, row) in enumerate(sub.iterrows()):
#             for j, col in enumerate(["Date","Open","High","Low","Close","Volume"]):
#                 val = row[col]
#                 txt = "" if pd.isna(val) else (val.strftime("%Y-%m-%d %H:%M") if col=="Date" else f"{val}")
#                 self.table.setItem(i, j, QTableWidgetItem(txt))
#
#     def get_datafeed(self):
#         """Return list of bt.feeds.PandasData created from current live_df"""
#         if self.data_rows == 0 or self.live_df.empty():
#             raise RuntimeError("No data loaded – start live feed or browse for CSV first.")
#         # prepare dataframe for bt
#         df = self.live_df.copy()
#         df.rename(columns={"Date":"datetime"}, inplace=True)
#         df.set_index("datetime", inplace=True)
#         df["openinterest"] = 0
#         feed = bt.feeds.PandasData(
#             dataname=df,
#             datetime=None,
#             open="Open", high="High", low="Low",
#             close="Close", volume="Volume", openinterest="openinterest"
#         )
#         return [feed]

# src/gui/ws_window.py

import pandas as pd
import yfinance as yf
import backtrader as bt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QSpinBox
)
from src.utils.logger import logger

class WsBacktestWindow(QWidget):
    """
    Window for live yfinance polling or CSV fallback, preview only.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # DataFrame storing Date, Open, High, Low, Close, Volume
        self.live_df = pd.DataFrame(columns=["Date","Open","High","Low","Close","Volume"])
        self.poll_timer = None
        self.engine = None

        # Default parameters
        self.ticker = "SPY"
        self.interval_min = 1
        self.data_rows = 0

        # Build UI
        layout = QVBoxLayout(self)
        ctrl = QHBoxLayout()
        layout.addLayout(ctrl)

        ctrl.addWidget(QLabel("Ticker:"))
        self.ticker_input = QLineEdit(self.ticker)
        ctrl.addWidget(self.ticker_input)

        ctrl.addWidget(QLabel("Interval (min):"))
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 60)
        self.interval_input.setValue(self.interval_min)
        ctrl.addWidget(self.interval_input)

        self.live_btn = QPushButton("Start Live Feed")
        self.live_btn.clicked.connect(self.on_toggle_live)
        ctrl.addWidget(self.live_btn)

        self.browse_btn = QPushButton("Browse CSV")
        self.browse_btn.clicked.connect(self.on_browse_csv)
        ctrl.addWidget(self.browse_btn)

        self.rowcount = QLabel("Rows: 0")
        ctrl.addWidget(self.rowcount)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Date","Open","High","Low","Close","Volume"])
        layout.addWidget(self.table)

    def on_toggle_live(self):
        # Start/stop polling
        if self.poll_timer and self.poll_timer.isActive():
            self.poll_timer.stop()
            self.poll_timer = None
            self.live_btn.setText("Start Live Feed")
            return

        ticker = self.ticker_input.text().strip().upper()
        if not ticker:
            QMessageBox.warning(self, "Input Error", "Enter a valid ticker.")
            return
        self.ticker = ticker
        # reset data
        self.live_df = self.live_df.iloc[0:0]
        self.data_rows = 0
        self.rowcount.setText("Rows: 0")
        self._refresh_table()

        # Begin polling every N minutes
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.fetch_live_data)
        self.fetch_live_data()
        self.poll_timer.start(self.interval_input.value() * 60 * 1000)
        self.live_btn.setText("Stop Live Feed")

    def fetch_live_data(self):
        try:
            # Use 2-day window to ensure multiple bars
            df = yf.download(
                tickers=self.ticker,
                period="2d",
                interval=f"{self.interval_input.value()}m",
                progress=False,
                prepost=False,
                auto_adjust=False
            )
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                # select ticker level if included
                if self.ticker in df.columns.get_level_values(1):
                    df = df.xs(self.ticker, axis=1, level=1)
                else:
                    df.columns = df.columns.get_level_values(0)
            # If no data, warn and exit
            if df.empty:
                QMessageBox.warning(self, "No Data", f"No data returned for {self.ticker}.")
                return

            # Prepare DataFrame
            df = df.copy()
            df.index.name = 'Date'
            df = df.reset_index()
            df = df[["Date","Open","High","Low","Close","Volume"]].dropna()
            # Volume zero indicates index or no trades

            # Append and dedupe
            self.live_df = pd.concat([self.live_df, df])\
                             .drop_duplicates(subset=["Date"])\
                             .sort_values("Date")
            self.data_rows = len(self.live_df)
            self.rowcount.setText(f"Rows: {self.data_rows}")
            self._refresh_table()

        except Exception as e:
            logger.exception(e)
            QMessageBox.critical(self, "Fetch Error", str(e))

    def on_browse_csv(self):
        # Fallback to CSV
        if self.poll_timer and self.poll_timer.isActive():
            self.poll_timer.stop()
            self.poll_timer = None
            self.live_btn.setText("Start Live Feed")

        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            df = pd.read_csv(path, parse_dates=["Date"] )
            df = df.sort_values("Date")[ ["Date","Open","High","Low","Close","Volume"] ]
            self.live_df = df
            self.data_rows = len(df)
            self.rowcount.setText(f"Rows: {self.data_rows}")
            self._refresh_table()
            QMessageBox.information(self, "Loaded", f"CSV loaded: {self.data_rows} rows.")
        except Exception as e:
            logger.exception(e)
            QMessageBox.critical(self, "Error", str(e))

    def _refresh_table(self):
        subset = self.live_df.tail(100)
        self.table.setRowCount(len(subset))
        for i, (_, row) in enumerate(subset.iterrows()):
            for j, col in enumerate(["Date","Open","High","Low","Close","Volume"]):
                val = row[col]
                if col == "Date":
                    dt = pd.to_datetime(val)
                    if dt.tzinfo is None:
                        dt = dt.tz_localize('UTC')
                    dt = dt.tz_convert('Asia/Kolkata')
                    txt = dt.strftime('%Y-%m-%d %H:%M')
                elif col == "Volume":
                    txt = "" if pd.isna(val) or val == 0 else str(int(val))
                else:
                    txt = "" if pd.isna(val) else f"{val:.2f}"
                self.table.setItem(i, j, QTableWidgetItem(txt))

    def get_datafeed(self):
        """Return a list containing a single Backtrader PandasData feed"""
        if self.data_rows == 0 or self.live_df.empty:
            raise RuntimeError("No data loaded – start live feed or browse for CSV first.")

        df = self.live_df.copy()
        df.rename(columns={"Date": "datetime"}, inplace=True)
        df.set_index("datetime", inplace=True)
        df["openinterest"] = 0
        feed = bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open="Open",
            high="High",
            low="Low",
            close="Close",
            volume="Volume",
            openinterest="openinterest"
        )
        return [feed]