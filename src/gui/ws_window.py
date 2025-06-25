# # src/gui/ws_window.py
#
# import sys
# import datetime
# import pandas as pd
# import yfinance as yf
# import backtrader as bt
#
# from PySide6.QtCore import Qt, QTimer
# from PySide6.QtWidgets import (
#     QWidget, QHBoxLayout, QVBoxLayout,
#     QPushButton, QFileDialog, QMessageBox,
#     QTableWidget, QTableWidgetItem, QTabWidget,
#     QLabel, QLineEdit, QSpinBox, QToolBar
# )
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavBar
#
# from src.data.loader import DataLoader
# from src.backtester.engine import BacktestEngine
# from src.backtester.strategies import (
#     SmaCross,
#     MultiTimeframeSma  # ensure this is imported
# )
# from src.gui.base_backtest_window import BaseBacktestWindow
# from src.viz.charts import MplCanvas
# from src.utils.logger import logger
#
#
# class WsBacktestWindow(BaseBacktestWindow):
#     """
#     Window for “live” yfinance feed (polled every N minutes) or CSV fallback.
#     - Tab 1: Data Preview (latest 100 bars in a table)
#     - Tab 2: Backtest Results (equity curve after “Run Backtest”)
#     A “Refresh” button in the toolbar clears everything and resets state.
#     """
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("WebSocket (yfinance) Backtester")
#
#         # ── State variables ──
#         self.live_df = pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
#         self.poll_timer = None
#         self.ticker = "SPY"
#         self.interval_min = 1
#         self.data_rows = 0
#         self.engine = None
#         self.current_strat_cls = None  # will store the selected strategy class
#
#         # ── Grab the HBox layout from BaseBacktestWindow ──
#         top_h_layout = self._main.layout()
#
#         # ── Hide the original chart & toolbar created by BaseBacktestWindow ──
#         self.chart.hide()
#         for child in self.findChildren(QToolBar):
#             child.hide()
#
#         # ── Create our QTabWidget in the right panel ──
#         self.tabs = QTabWidget(self)
#         top_h_layout.addWidget(self.tabs, 3)
#
#         # --- Tab: Data Preview ---
#         self.preview_widget = QWidget()
#         self.preview_layout = QVBoxLayout(self.preview_widget)
#         self.tabs.addTab(self.preview_widget, "Data Preview")
#
#         # --- Tab: Backtest Results (initially disabled) ---
#         self.results_widget = QWidget()
#         self.results_layout = QVBoxLayout(self.results_widget)
#         self.tabs.addTab(self.results_widget, "Backtest Results")
#         self.results_widget.setEnabled(False)
#
#         # ── Build UI for Data Preview ──
#         self._build_data_preview_ui()
#
#         # ── Build UI for Backtest Results ──
#         self._build_results_ui()
#
#         # ── Add Refresh button to a new toolbar at the top ──
#         self.refresh_toolbar = QToolBar("Controls", self)
#         self.addToolBar(Qt.TopToolBarArea, self.refresh_toolbar)
#         refresh_btn = QPushButton("Refresh")
#         refresh_btn.clicked.connect(self.on_refresh)
#         self.refresh_toolbar.addWidget(refresh_btn)
#
#     def add_data_controls(self):
#         """
#         Override of BaseBacktestWindow.add_data_controls().
#         All controls live in _build_data_preview_ui(), so this remains empty.
#         """
#         pass
#
#     def _build_data_preview_ui(self):
#         """
#         Left portion of Data Preview: ticker, interval, Start/Stop, Browse CSV.
#         Right portion: QTableWidget showing up to the last 100 rows of self.live_df.
#         """
#         controls_layout = QHBoxLayout()
#         self.preview_layout.addLayout(controls_layout)
#
#         controls_layout.addWidget(QLabel("Ticker:"))
#         self.ticker_input = QLineEdit(self.ticker)
#         controls_layout.addWidget(self.ticker_input)
#
#         controls_layout.addWidget(QLabel("Interval (min):"))
#         self.interval_input = QSpinBox()
#         self.interval_input.setRange(1, 60)
#         self.interval_input.setValue(self.interval_min)
#         controls_layout.addWidget(self.interval_input)
#
#         self.live_btn = QPushButton("Start Live Feed")
#         self.live_btn.clicked.connect(self.on_toggle_live)
#         controls_layout.addWidget(self.live_btn)
#
#         self.browse_button = QPushButton("Browse CSV for Backtest")
#         self.browse_button.clicked.connect(self.on_browse_csv)
#         controls_layout.addWidget(self.browse_button)
#
#         self.rowcount_label = QLabel("Rows: 0")
#         controls_layout.addWidget(self.rowcount_label)
#
#         self.table = QTableWidget(0, 6)
#         self.table.setHorizontalHeaderLabels(["Date", "Open", "High", "Low", "Close", "Volume"])
#         self.preview_layout.addWidget(self.table)
#
#     def on_toggle_live(self):
#         """
#         Start or stop the QTimer that polls yfinance. If the timer is active, stop it;
#         otherwise, start a fresh timer and begin fetching data immediately.
#         """
#         if self.poll_timer and self.poll_timer.isActive():
#             self.poll_timer.stop()
#             self.poll_timer.deleteLater()
#             self.poll_timer = None
#             self.live_btn.setText("Start Live Feed")
#             return
#
#         self.ticker = self.ticker_input.text().strip().upper()
#         self.interval_min = self.interval_input.value()
#         if not self.ticker:
#             QMessageBox.warning(self, "Input Error", "Please enter a valid ticker.")
#             return
#
#         # Reset DataFrame & table
#         self.live_df = pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
#         self.data_rows = 0
#         self.rowcount_label.setText("Rows: 0")
#         self._refresh_table()
#
#         # Start polling yfinance every interval_min minutes
#         self.poll_timer = QTimer(self)
#         self.poll_timer.timeout.connect(self.fetch_live_data)
#         self.fetch_live_data()  # first immediate fetch
#         self.poll_timer.start(self.interval_min * 60 * 1000)
#         self.live_btn.setText("Stop Live Feed")
#
#     def fetch_live_data(self):
#         """
#         Poll yfinance for the last 1 day of bars at the chosen interval. Append new rows,
#         drop duplicates, sort by date, then refresh the table and row count.
#         """
#         try:
#             df = yf.download(
#                 self.ticker,
#                 period="1d",
#                 interval=f"{self.interval_min}m",
#                 progress=False,
#                 prepost=False,
#             )
#             if df.empty:
#                 return
#
#             df = df.reset_index()
#             df.rename(columns={"Datetime": "Date"}, inplace=True)
#             df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
#
#             combined = pd.concat([self.live_df, df], ignore_index=True)
#             combined.drop_duplicates(subset=["Date"], keep="last", inplace=True)
#             combined.sort_values("Date", inplace=True)
#
#             self.live_df = combined
#             self.data_rows = len(self.live_df)
#             self.rowcount_label.setText(f"Rows: {self.data_rows}")
#             self._refresh_table()
#
#         except Exception as e:
#             logger.exception(f"Error fetching live data: {e}")
#
#     def _refresh_table(self):
#         """
#         Populate (up to) the last 100 rows of self.live_df into QTableWidget.
#         - If “Date” is NaT or cannot be parsed, leave blank.
#         - If “Volume” is NaN, leave blank.
#         """
#         subset = self.live_df.tail(100).copy()
#         self.table.setRowCount(len(subset))
#
#         for r, (_, row) in enumerate(subset.iterrows()):
#             # ── Handle the “Date” column ──
#             date_val = row["Date"]
#             if pd.isna(date_val):
#                 date_str = ""
#             else:
#                 if not isinstance(date_val, pd.Timestamp):
#                     try:
#                         date_val = pd.to_datetime(date_val)
#                         date_str = date_val.strftime("%Y-%m-%d %H:%M")
#                     except Exception:
#                         date_str = str(date_val)
#                 else:
#                     date_str = date_val.strftime("%Y-%m-%d %H:%M")
#
#             self.table.setItem(r, 0, QTableWidgetItem(date_str))
#
#             # ── Handle numeric columns (Open, High, Low, Close) ──
#             # They should always be floats; if NaN, show empty string.
#             for c_idx, col in enumerate(["Open", "High", "Low", "Close"], start=1):
#                 val = row[col]
#                 if pd.isna(val):
#                     text = ""
#                 else:
#                     text = f"{val:.2f}"
#                 self.table.setItem(r, c_idx, QTableWidgetItem(text))
#
#             # ── Handle the “Volume” column ──
#             vol_val = row["Volume"]
#             if pd.isna(vol_val):
#                 vol_str = ""
#             else:
#                 try:
#                     vol_str = str(int(vol_val))
#                 except Exception:
#                     vol_str = str(vol_val)
#             self.table.setItem(r, 5, QTableWidgetItem(vol_str))
#
#         # Adjust column widths to fit content
#         self.table.resizeColumnsToContents()
#
#     def on_browse_csv(self):
#         """
#         Stop live polling (if active), read a local CSV, and replace self.live_df with it.
#         Initialize a new BacktestEngine so that run_backtest() sees data has been loaded.
#         """
#         if self.poll_timer and self.poll_timer.isActive():
#             self.poll_timer.stop()
#             self.poll_timer.deleteLater()
#             self.poll_timer = None
#             self.live_btn.setText("Start Live Feed")
#
#         path, _ = QFileDialog.getOpenFileName(
#             self, "Select CSV File for Backtest", "", "CSV Files (*.csv)"
#         )
#         if not path:
#             return
#
#         try:
#             df = pd.read_csv(
#                 path,
#                 parse_dates=["Date"],
#                 dtype={"Open": float, "High": float, "Low": float, "Close": float, "Volume": int}
#             )
#             df.sort_values("Date", inplace=True)
#             df["openinterest"] = 0
#
#             # Keep only columns needed for preview
#             self.live_df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
#             self.data_rows = len(self.live_df)
#             self.rowcount_label.setText(f"Rows: {self.data_rows}")
#             self._refresh_table()
#
#             self.engine = BacktestEngine()
#             QMessageBox.information(
#                 self,
#                 "CSV Loaded for Backtest",
#                 f"Loaded CSV: {path}\n{self.data_rows} bars available."
#             )
#         except Exception as e:
#             logger.exception(f"Error loading CSV: {e}")
#             QMessageBox.critical(self, "Error", str(e))
#
#     def attach_data_feed_to_engine(self):
#         """
#         Convert self.live_df into a backtrader PandasData feed.
#         If the chosen strategy is MultiTimeframeSma, also create and add a weekly feed.
#         """
#         # 1) Always add the daily feed
#         df_daily = self.live_df.copy()
#         df_daily.rename(columns={"Date": "datetime"}, inplace=True)
#         df_daily.set_index("datetime", inplace=True)
#         df_daily["openinterest"] = 0
#
#         daily_feed = bt.feeds.PandasData(
#             dataname=df_daily,
#             datetime=None,
#             open="Open",
#             high="High",
#             low="Low",
#             close="Close",
#             volume="Volume",
#             openinterest="openinterest"
#         )
#         self.engine.add_data(daily_feed)
#
#         # 2) If running MultiTimeframeSma, also build a weekly resampled feed
#         if self.current_strat_cls is MultiTimeframeSma:
#             # Resample to weekly OHLCV
#             df_weekly = df_daily.resample("W").agg({
#                 "Open": "first",
#                 "High": "max",
#                 "Low": "min",
#                 "Close": "last",
#                 "Volume": "sum",
#                 "openinterest": "last"
#             }).dropna()
#
#             weekly_feed = bt.feeds.PandasData(
#                 dataname=df_weekly,
#                 datetime=None,
#                 open="Open",
#                 high="High",
#                 low="Low",
#                 close="Close",
#                 volume="Volume",
#                 openinterest="openinterest"
#             )
#             self.engine.add_data(weekly_feed)
#
#     def on_refresh(self):
#         """
#         Stop any polling, clear DataFrame & table, disable results tab, and reset engine.
#         """
#         if self.poll_timer and self.poll_timer.isActive():
#             self.poll_timer.stop()
#             self.poll_timer.deleteLater()
#             self.poll_timer = None
#             self.live_btn.setText("Start Live Feed")
#
#         self.live_df = pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
#         self.data_rows = 0
#         self.rowcount_label.setText("Rows: 0")
#         self._refresh_table()
#
#         self.engine = None
#         self.results_widget.setEnabled(False)
#         self.equity_canvas.axes.clear()
#         self.equity_canvas.draw()
#
#         QMessageBox.information(self, "Refreshed", "All data and results have been cleared.")
#
#     def run_backtest(self):
#         """
#         Overrides BaseBacktestWindow.run_backtest to:
#         1) Ensure data is loaded (engine != None, data_rows set)
#         2) Remember which strategy was selected
#         3) Create a fresh BacktestEngine, attach feeds (daily + weekly if needed),
#            configure the strategy + TimeReturn analyzer, run Cerebro,
#            and plot the equity curve on the "Backtest Results" tab.
#         """
#         # 1) Must have loaded data already
#         if not self.engine or self.data_rows is None:
#             QMessageBox.warning(self, "Warning", "Load data first.")
#             return
#
#         # 2) Get chosen strategy class & parameters
#         strat_cls, strat_params = self.strategy_selector.get_strategy()
#         self.current_strat_cls = strat_cls  # remember for attach_data_feed_to_engine()
#
#         fast_p = strat_params.get("fast", 0)
#         slow_p = strat_params.get("slow", 0)
#         # If strategy uses an SMA slow period, ensure enough bars
#         if slow_p > 0 and self.data_rows < slow_p:
#             QMessageBox.warning(
#                 self, "Data Too Short",
#                 f"Your data has {self.data_rows} bars, but SMA long period is {slow_p}.\n"
#                 "Reduce period or load more data."
#             )
#             return
#
#         try:
#             # 3) Reinitialize a fresh engine
#             self.engine = BacktestEngine()
#
#             # 4) Attach daily feed (and weekly if MultiTimeframeSma)
#             self.attach_data_feed_to_engine()
#
#             # 5) Configure strategy and analyzer
#             self.engine.set_strategy(strat_cls, **strat_params)
#             self.engine.add_analyzer(bt.analyzers.TimeReturn, _name="timereturn")
#
#             # 6) Run Cerebro
#             strategies = self.engine.run()
#             strat = strategies[0]
#
#             # 7) Build equity curve from TimeReturn
#             tr = strat.analyzers.timereturn.get_analysis()
#             if not tr:
#                 QMessageBox.warning(self, "No Data", "No TimeReturn data to plot.")
#                 return
#
#             dates = []
#             equity = []
#             start_cash = self.engine.cerebro.broker.getvalue()
#             cum_val = start_cash
#
#             for dt, ret in sorted(tr.items()):
#                 if isinstance(dt, datetime.date):
#                     dates.append(dt)
#                 else:
#                     dates.append(dt.date())
#                 cum_val *= (1 + ret)
#                 equity.append(cum_val)
#
#             # 8) Plot in “Backtest Results” tab
#             self.results_widget.setEnabled(True)
#             self.equity_canvas.axes.clear()
#             self.equity_canvas.axes.plot(
#                 dates,
#                 equity,
#                 marker="o",
#                 linestyle="-",
#                 label="Equity Curve"
#             )
#             self.equity_canvas.axes.set_title("Backtest Equity Curve")
#             self.equity_canvas.axes.set_xlabel("Date")
#             self.equity_canvas.axes.set_ylabel("Portfolio Value")
#             self.equity_canvas.axes.legend()
#             self.equity_canvas.draw()
#
#             # Switch to the Backtest Results tab
#             self.tabs.setCurrentWidget(self.results_widget)
#
#         except Exception as e:
#             logger.exception("Backtest failed")
#             QMessageBox.critical(self, "Error running backtest", str(e))
#
#     def get_datafeed(self):
#         """
#         Prepare a fresh BacktestEngine, attach the live (or CSV) feeds,
#         :return: the primary (first) data feed.
#         """
#
#         if self.data_rows == 0:
#             raise RuntimeError("No data loaded – start live feed or browse for CSV first.")
#
#         #create a temp engine
#         self.engine = BacktestEngine()
#         strat_cls, _ = self.strategy_selector.get_strategy()
#         self.current_strat_cls = strat_cls
#         self.attach_data_feed_to_engine()
#         return list(self.engine.cerebro.datas)
#
# # For standalone testing
# if __name__ == "__main__":
#     from PySide6.QtWidgets import QApplication
#     app = QApplication(sys.argv)
#     w = WsBacktestWindow()
#     w.show()
#     sys.exit(app.exec())



# src/gui/ws_window.py

import sys
import pandas as pd
import yfinance as yf
import backtrader as bt
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QSpinBox
)
from src.backtester.engine import BacktestEngine
from src.utils.logger import logger

class WsBacktestWindow(QWidget):
    """
    Simplified window for live CSV or yfinance feed preview.
    Inherits only data loading; backtest run handled by MainWindow.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.live_df = pd.DataFrame(columns=["Date","Open","High","Low","Close","Volume"])
        self.poll_timer = None
        self.ticker = "SPY"
        self.interval_min = 1
        self.data_rows = 0
        self.engine = None

        layout = QVBoxLayout(self)
        ctrl = QHBoxLayout()
        layout.addLayout(ctrl)

        ctrl.addWidget(QLabel("Ticker:"))
        self.ticker_input = QLineEdit(self.ticker)
        ctrl.addWidget(self.ticker_input)

        ctrl.addWidget(QLabel("Interval (min):"))
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1,60)
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

        self.table = QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(["Date","Open","High","Low","Close","Volume"])
        layout.addWidget(self.table)

    def on_toggle_live(self):
        if self.poll_timer and self.poll_timer.isActive():
            self.poll_timer.stop()
            self.poll_timer = None
            self.live_btn.setText("Start Live Feed")
            return
        self.ticker = self.ticker_input.text().strip().upper()
        if not self.ticker:
            QMessageBox.warning(self, "Input Error", "Enter a valid ticker.")
            return
        self.live_df = self.live_df.iloc[0:0]
        self.data_rows = 0
        self.rowcount.setText("Rows: 0")
        self._refresh_table()
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.fetch_live_data)
        self.fetch_live_data()
        self.poll_timer.start(self.interval_input.value()*60*1000)
        self.live_btn.setText("Stop Live Feed")

    def fetch_live_data(self):
        try:
            df = yf.download(self.ticker, period="1d", interval=f"{self.interval_input.value()}m", progress=False)
            if df.empty: return
            df = df.reset_index()[["Datetime","Open","High","Low","Close","Volume"]]
            df.rename(columns={"Datetime":"Date"}, inplace=True)
            combined = pd.concat([self.live_df, df]).drop_duplicates(subset=["Date"]).sort_values("Date")
            self.live_df = combined
            self.data_rows = len(combined)
            self.rowcount.setText(f"Rows: {self.data_rows}")
            self._refresh_table()
        except Exception as e:
            logger.exception(e)

    def on_browse_csv(self):
        if self.poll_timer and self.poll_timer.isActive():
            self.poll_timer.stop()
            self.poll_timer = None
            self.live_btn.setText("Start Live Feed")
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if not path: return
        try:
            df = pd.read_csv(path, parse_dates=["Date"] )
            df = df.sort_values("Date")[ ["Date","Open","High","Low","Close","Volume"] ]
            self.live_df = df
            self.data_rows = len(df)
            self.rowcount.setText(f"Rows: {self.data_rows}")
            self._refresh_table()
            self.engine = BacktestEngine()
            QMessageBox.information(self, "Loaded", f"CSV loaded: {self.data_rows} rows.")
        except Exception as e:
            logger.exception(e)
            QMessageBox.critical(self, "Error", str(e))

    def _refresh_table(self):
        sub = self.live_df.tail(100)
        self.table.setRowCount(len(sub))
        for i, (_, row) in enumerate(sub.iterrows()):
            for j, col in enumerate(["Date","Open","High","Low","Close","Volume"]):
                val = row[col]
                txt = "" if pd.isna(val) else (val.strftime("%Y-%m-%d %H:%M") if col=="Date" else f"{val}")
                self.table.setItem(i, j, QTableWidgetItem(txt))

    def get_datafeed(self):
        """Return list of bt.feeds.PandasData created from current live_df"""
        if self.data_rows == 0:
            raise RuntimeError("No data loaded – start live feed or browse for CSV first.")
        # prepare dataframe for bt
        df = self.live_df.copy()
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