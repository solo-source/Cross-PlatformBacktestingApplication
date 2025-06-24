# # src/gui/main_window.py
# """
# MainWindow: PySide6 GUI to load data, run backtests, and view results.
# """
#
# import sys
# import datetime
# import pandas as pd
# import backtrader as bt
# from PySide6.QtWidgets import (
#     QApplication, QMainWindow, QFileDialog, QMessageBox,
#     QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
#     QPushButton, QSplitter
# )
# from PySide6.QtCore import Qt
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
#
# from src.gui.strategy_selector import StrategySelectorWidget
# from src.utils.logger import logger
# from src.data.loader import DataLoader
# from src.data.stream import RestStreamer, WebSocketStreamer
# from src.backtester.engine import BacktestEngine
# from src.viz.charts import MplCanvas
# from src.backtester.strategies import MultiTimeframeSma
#
#
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Cross-Platform Backtester")
#         self.resize(1200, 800)
#
#         # --- Central Layout ---
#         main_widget = QWidget()
#         self.setCentralWidget(main_widget)
#
#         splitter = QSplitter()
#         splitter.setOrientation(Qt.Horizontal)
#
#         # Left panel
#         left_panel = QWidget()
#         left_layout = QVBoxLayout(left_panel)
#
#         # Data loader form
#         data_form = QFormLayout()
#         self.csv_btn = QPushButton("Load CSV")
#         self.csv_btn.clicked.connect(self.load_csv)
#         data_form.addRow("Historical Data:", self.csv_btn)
#
#         self.rest_btn = QPushButton("Start REST Stream")
#         self.rest_btn.clicked.connect(self.start_rest)
#         data_form.addRow("REST Stream:", self.rest_btn)
#
#         self.ws_btn = QPushButton("Start WS Stream")
#         self.ws_btn.clicked.connect(self.start_ws)
#         data_form.addRow("WebSocket Stream:", self.ws_btn)
#
#         left_layout.addLayout(data_form)
#
#         # Strategy selector
#         self.strategy_selector = StrategySelectorWidget()
#         left_layout.addWidget(self.strategy_selector)
#
#         # Run button
#         self.run_btn = QPushButton("Run Backtest")
#         self.run_btn.clicked.connect(self.run_backtest)
#         left_layout.addWidget(self.run_btn)
#
#         left_layout.addStretch()
#         splitter.addWidget(left_panel)
#
#         # Right panel: chart + toolbar
#         right_panel = QWidget()
#         right_layout = QVBoxLayout(right_panel)
#
#         self.chart = MplCanvas(self, width=5, height=4, dpi=100)
#         self.toolbar = NavigationToolbar(self.chart, self)
#         right_layout.addWidget(self.toolbar)
#         right_layout.addWidget(self.chart)
#
#         splitter.addWidget(right_panel)
#         splitter.setStretchFactor(1, 3)
#
#         main_layout = QHBoxLayout(main_widget)
#         main_layout.addWidget(splitter)
#
#         # Engine and state
#         self.engine = None
#         self.data_rows = None
#         self.rest_streamer = None
#         self.ws_streamer = None
#
#     def load_csv(self):
#         path, _ = QFileDialog.getOpenFileName(
#             self, "Open CSV File", "", "CSV Files (*.csv)"
#         )
#         if not path:
#             return
#
#         try:
#             # Only store the path and row count
#             _, row_count = DataLoader.from_csv(path)
#             self.csv_path = path
#             self.data_rows = row_count
#
#             QMessageBox.information(
#                 self, "Success",
#                 f"Loaded CSV: {path}\n{row_count} bars available."
#             )
#
#         except Exception as e:
#             logger.exception("Failed to load CSV")
#             QMessageBox.critical(self, "Error", str(e))
#
#     def start_rest(self):
#         url, _ = QFileDialog.getOpenFileName(
#             self, "Enter REST URL (in a text file)", "", "Text Files (*.txt)"
#         )
#         if not url:
#             return
#         try:
#             rest_url = open(url).read().strip()
#             self.rest_streamer = RestStreamer(rest_url, interval_s=5)
#             self.rest_streamer.new_data.connect(self.on_live_data)
#             self.rest_streamer.start()
#             QMessageBox.information(self, "REST", f"Polling {rest_url}")
#         except Exception as e:
#             logger.exception("Failed to start REST streamer")
#             QMessageBox.critical(self, "Error", str(e))
#
#     def start_ws(self):
#         try:
#             ws_url = "wss://stream.binance.com:9443/ws"
#             subscribe = {"method":"SUBSCRIBE","params":["btcusdt@trade"],"id":1}
#             self.ws_streamer = WebSocketStreamer(ws_url, subscribe)
#             self.ws_streamer.new_data.connect(self.on_live_data)
#             self.ws_streamer.start()
#             QMessageBox.information(self, "WebSocket", f"Streaming {ws_url}")
#         except Exception as e:
#             logger.exception("Failed to start WebSocket streamer")
#             QMessageBox.critical(self, "Error", str(e))
#
#     def on_live_data(self, data: dict):
#         # TODO: convert to live Backtrader feed or real-time plot update
#         print("Live data:", data)
#
#     def run_backtest(self):
#         print(">>> run_backtest() start")
#         logger.info("=== Starting backtest ===")
#
#         # 0) Preconditions
#         if not hasattr(self, 'csv_path') or self.csv_path is None:
#             logger.error("No csv_path in MainWindow")
#             QMessageBox.warning(self, "Warning", "Load data first.")
#             return
#
#         # 1) Strategy selection
#         strat_cls, strat_params = self.strategy_selector.get_strategy()
#         print(f"Selected strategy: {strat_cls.__name__}, params: {strat_params}")
#         logger.info(f"Selected strategy: {strat_cls.__name__}, params: {strat_params}")
#
#         # 2) Re-create engine
#         self.engine = BacktestEngine()
#         print("Engine re-created")
#         logger.debug("Engine re-created")
#
#         # 3) Read CSV into DataFrame
#         try:
#             df = pd.read_csv(self.csv_path, parse_dates=['Date'])
#             df.sort_values('Date', inplace=True)
#             print(f"CSV reloaded, {len(df)} rows")
#             logger.debug(f"CSV reloaded, {len(df)} rows")
#         except Exception as e:
#             logger.exception("Failed to read CSV")
#             QMessageBox.critical(self, "Error", f"CSV load error:\n{e}")
#             return
#
#         # 4) Build daily feed
#         df_daily = df.rename(columns={'Date': 'datetime'}).copy()
#         df_daily['openinterest'] = 0
#         daily_feed = bt.feeds.PandasData(
#             dataname=df_daily,
#             datetime='datetime',
#             open='Open', high='High',
#             low='Low', close='Close',
#             volume='Volume', openinterest='openinterest'
#         )
#         self.engine.add_data(daily_feed)
#         print("Added daily feed")
#         logger.debug("Added daily feed")
#
#         # 5) If multi-TF, build and add weekly feed
#         if strat_cls is MultiTimeframeSma:
#             df_weekly = (
#                 df.set_index('Date')
#                 .resample('W')
#                 .agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
#                 .dropna()
#                 .reset_index()
#                 .rename(columns={'Date': 'datetime'})
#             )
#             df_weekly['openinterest'] = 0
#             weekly_feed = bt.feeds.PandasData(
#                 dataname=df_weekly,
#                 datetime='datetime',
#                 open='Open', high='High',
#                 low='Low', close='Close',
#                 volume='Volume', openinterest='openinterest'
#             )
#             self.engine.add_data(weekly_feed)
#             print("Added weekly feed for MultiTimeframeSma")
#             logger.debug("Added weekly feed for MultiTimeframeSma")
#
#         # 6) Set strategy & analyzer
#         self.engine.set_strategy(strat_cls, **strat_params)
#         self.engine.add_analyzer(bt.analyzers.TimeReturn, _name='timereturn')
#         print("Strategy and analyzer registered")
#         logger.debug("Strategy and analyzer registered")
#
#         # 7) Debug: inspect cerebro before run
#         cb = self.engine.cerebro
#         print(f"Cerebro has {len(cb.datas)} data feeds")
#         logger.info(f"Cerebro has {len(cb.datas)} data feeds")
#
#         # 8) Run
#         try:
#             results = cb.run()
#             print("Cerebro.run() returned:", results)
#             logger.info(f"Cerebro.run() returned: {results}")
#         except Exception as e:
#             logger.exception("Backtest run error")
#             QMessageBox.critical(self, "Error", f"Backtest error:\n{e}")
#             return
#
#         # 9) Check results
#         if not results:
#             print("No strategies returned")
#             logger.warning("No strategies returned")
#             QMessageBox.warning(self, "No Strategy",
#                                 "Cerebro.run() returned no strategy instances.")
#             return
#
#         strat = results[0]
#         print("Got strategy instance:", strat)
#         logger.info(f"Got strategy instance: {strat}")
#
#         # 10) Build and plot equity curve
#         tr = strat.analyzers.timereturn.get_analysis()
#         if not tr:
#             QMessageBox.warning(self, "No Data", "No return data from analyzer.")
#             return
#
#         dates, equity = [], []
#         cum_val = cb.broker.startingcash
#         for dt, ret in sorted(tr.items()):
#             dates.append(dt if hasattr(dt, 'date') else dt.date())
#             cum_val *= (1 + ret)
#             equity.append(cum_val)
#
#         self.chart.axes.clear()
#         self.chart.axes.plot(dates, equity, marker='o', linestyle='-')
#         self.chart.axes.set_title(f"Equity Curve: {strat_cls.__name__}")
#         self.chart.axes.set_xlabel("Date")
#         self.chart.axes.set_ylabel("Portfolio Value")
#         self.chart.draw()
#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     w = MainWindow()
#     w.show()
#     sys.exit(app.exec())

# src/gui/main.py


# # src/gui/main_window.py
import sys
from PySide6.QtWidgets import QApplication
from src.gui.data_source_dialog import DataSourceDialog
from src.gui.csv_window import CsvBacktestWindow
from src.gui.rest_window import RestBacktestWindow
from src.gui.ws_window import WsBacktestWindow

def main():
    app = QApplication(sys.argv)

    # 1) Show the data‐source selection dialog
    dlg = DataSourceDialog()
    if dlg.exec() != DataSourceDialog.Accepted:
        sys.exit(0)

    choice = dlg.selected_option()
    if choice == DataSourceDialog.OPTION_CSV:
        window = CsvBacktestWindow()
    elif choice == DataSourceDialog.OPTION_REST:
        window = RestBacktestWindow()
    else:  # DataSourceDialog.OPTION_WS
        window = WsBacktestWindow()

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
