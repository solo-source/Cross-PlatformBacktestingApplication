# src/gui/base_backtest_window.py

import datetime

import backtrader as bt
from backtrader import num2date
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QFormLayout,
    QPushButton, QMessageBox, QVBoxLayout
)
from PySide6.QtWidgets import QToolBar
from PySide6.QtCore import Qt, QSize
from src.utils.logger import logger
from src.backtester.engine import BacktestEngine
from src.gui.strategy_selector import StrategySelectorWidget
from src.viz.charts import MplCanvas

# Import the Matplotlib NavigationToolbar
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


class BaseBacktestWindow(QMainWindow):
    """
    Base window that contains:
      - A StrategySelectorWidget
      - A “Run Backtest” button
      - A chart area (MplCanvas with toolbar)
      - (Data-loading controls are left abstract, to be implemented by subclasses)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modular Backtester")
        self.resize(1200, 800)

        self.engine = None
        self.data_rows = None  # number of bars loaded (used for length checks)

        # Central widget layout
        self._main = QWidget()
        self.setCentralWidget(self._main)
        h_layout = QHBoxLayout(self._main)

        # Left panel: strategy selection + run button + (data‐loading placeholder)
        self.left_panel = QWidget()
        self.left_layout = QFormLayout(self.left_panel)
        h_layout.addWidget(self.left_panel, 1)

        # Placeholder for data-feed controls; subclasses override `add_data_controls()`
        self.add_data_controls()

        # Strategy selector widget (populates with all available strategies)
        self.strategy_selector = StrategySelectorWidget(self)
        self.left_layout.addRow(self.strategy_selector)

        # “Run Backtest” button
        self.run_button = QPushButton("Run Backtest", self)
        self.run_button.clicked.connect(self.run_backtest)
        self.left_layout.addRow(self.run_button)

        # Right panel: chart + navigation toolbar
        right_container = QWidget()
        right_vlayout = QVBoxLayout(right_container)
        h_layout.addWidget(right_container, 3)

        # Matplotlib canvas
        self.chart = MplCanvas(self, width=5, height=4, dpi=100)
        right_vlayout.addWidget(self.chart)

        # Add Matplotlib navigation toolbar
        toolbar = QToolBar("Chart Controls", self)
        right_vlayout.addWidget(toolbar)
        toolbar.setIconSize(QSize(16, 16))
        nav = NavigationToolbar(self.chart, self)
        toolbar.addWidget(nav)

    def add_data_controls(self):
        """
        Abstract method: subclasses should add their own data‐loading controls
        (e.g., CSV “Browse” button, REST URL input, WS subscription, etc.)
        """
        raise NotImplementedError("Subclasses must implement add_data_controls()")

    # def run_backtest(self):
    #     """
    #     Common “Run Backtest” logic. Subclasses must ensure that
    #     `self.engine` and `self.data_rows` have been set by data-loading steps.
    #     """
    #     # 1) proof that data has been loaded
    #     if not self.engine or self.data_rows is None:
    #         QMessageBox.warning(self, "Warning", "Load data first.")
    #         return
    #
    #     # 2) Get selected strategy & parameters
    #     strat_cls, strat_params = self.strategy_selector.get_strategy()
    #     # Extract fast/slow for length check (if they exist)
    #     fast_p = strat_params.get("fast", 0)
    #     slow_p = strat_params.get("slow", 0)
    #
    #     # 3) Check that data length ≥ slow_p (if slow_p is defined)
    #     if slow_p > 0 and self.data_rows < slow_p:
    #         QMessageBox.warning(
    #             self, "Data Too Short",
    #             f"Your data has {self.data_rows} bars, but SMA long period is {slow_p}.\n"
    #             "Reduce period or load more data."
    #         )
    #         return
    #
    #     try:
    #         # 4) Re‐initialize engine from scratch
    #         self.engine = BacktestEngine()
    #
    #         # 5) Add the chosen data feed(s) to engine (subclass must implement)
    #         self.attach_data_feed_to_engine()
    #
    #         # 6) Configure strategy & add TimeReturn analyzer
    #         self.engine.set_strategy(strat_cls, **strat_params)
    #         self.engine.add_analyzer(bt.analyzers.TimeReturn, _name="timereturn")
    #
    #         # 7) Run the engine
    #         strategies = self.engine.run()
    #         strat = strategies[0]
    #
    #         # 8) Build equity curve from TimeReturn
    #         tr = strat.analyzers.timereturn.get_analysis()
    #         if not tr:
    #             QMessageBox.warning(self, "No Data", "No TimeReturn data to plot.")
    #             return
    #
    #         dates = []
    #         equity = []
    #         # Get starting cash
    #         start_cash = self.engine.cerebro.broker.getvalue()
    #         cum_value = start_cash
    #
    #         # Build cumulative equity curve
    #         for dt, ret in sorted(tr.items()):
    #             # dt can be datetime or date
    #             if isinstance(dt, datetime.date):
    #                 dates.append(dt)
    #             else:
    #                 dates.append(dt.date())
    #             cum_value *= (1 + ret)
    #             equity.append(cum_value)
    #
    #         # 9) Plot equity curve
    #         self.chart.axes.clear()
    #         self.chart.axes.plot(
    #             dates,
    #             equity,
    #             marker="o",
    #             linestyle="-",
    #             label="Equity Curve"
    #         )
    #         self.chart.axes.set_title("Backtest Equity Curve")
    #         self.chart.axes.set_xlabel("Date")
    #         self.chart.axes.set_ylabel("Portfolio Value")
    #         self.chart.axes.legend()
    #         self.chart.draw()
    #
    #     except Exception as e:
    #         logger.exception("Backtest failed")
    #         QMessageBox.critical(self, "Error running backtest", str(e))
    def run_backtest(self):
        """
        Common “Run Backtest” logic. Subclasses must ensure that
        `self.engine` and `self.data_rows` have been set by data‐loading steps.
        """
        # 1) Make sure data has already been loaded
        if not self.engine or self.data_rows is None:
            QMessageBox.warning(self, "Warning", "Load data first.")
            return

        # 2) Get the user’s chosen strategy class and parameter dict
        strat_cls, strat_params = self.strategy_selector.get_strategy()
        # Extract fast/slow so we can verify data length if needed
        fast_p = strat_params.get("fast", 0)
        slow_p = strat_params.get("slow", 0)

        # 3) If the selected strategy uses an SMA “slow” period, ensure enough bars
        if slow_p > 0 and self.data_rows < slow_p:
            QMessageBox.warning(
                self,
                "Data Too Short",
                f"Your data has {self.data_rows} bars, but SMA long period is {slow_p}.\n"
                "Reduce period or load more data."
            )
            return

        try:
            # 4) Create a fresh BacktestEngine (which already attaches BuySell observer)
            self.engine = BacktestEngine()

            # 5) Attach the chosen data feed(s) to the engine
            #    (Subclass must implement attach_data_feed_to_engine())
            self.attach_data_feed_to_engine()

            # 6) Force printlog=True so that strategy.log(...) lines appear
            strat_params.setdefault("printlog", True)

            # 7) Add the strategy to Cerebro
            self.engine.set_strategy(strat_cls, **strat_params)

            # 8) Add TimeReturn Analyzer (so we can build an equity curve)
            self.engine.add_analyzer(bt.analyzers.TimeReturn, _name="timereturn")

            # 9) Run the backtest
            strategies = self.engine.run()
            strat = strategies[0]

            # 10) Retrieve the TimeReturn analysis
            tr = strat.analyzers.timereturn.get_analysis()
            if not tr:
                QMessageBox.warning(self, "No Data", "No TimeReturn data to plot.")
                return

            # 11) Build date‐series and cumulative equity
            dates = []
            equity = []
            start_cash = self.engine.cerebro.broker.getvalue()
            cum_value = start_cash

            for dt, ret in sorted(tr.items()):
                # Convert dt → a plain date if needed
                if isinstance(dt, datetime.date):
                    dates.append(dt)
                else:
                    dates.append(dt.date())

                cum_value *= (1 + ret)
                equity.append(cum_value)

            # 12) Plot the equity curve on our Matplotlib canvas
            self.chart.axes.clear()
            self.chart.axes.plot(
                dates,
                equity,
                marker="o",
                linestyle="-",
                label="Equity Curve"
            )
            self.chart.axes.set_title("Backtest Equity Curve")
            self.chart.axes.set_xlabel("Date")
            self.chart.axes.set_ylabel("Portfolio Value")
            self.chart.axes.legend()
            self.chart.draw()

            # 13) Switch the GUI over to the “Results” tab if you have one
            try:
                self.tabs.setCurrentWidget(self.results_widget)
            except AttributeError:
                # If this particular window does not have tabs, ignore
                pass

        except Exception as e:
            logger.exception("Backtest failed")
            QMessageBox.critical(self, "Error running backtest", str(e))


    def attach_data_feed_to_engine(self):
        """
        Abstract method: subclasses must add their specific data feed(s) to `self.engine`.
        After this method, `self.engine` should already be a fresh BacktestEngine()
        with exactly one (or more) data feeds attached.
        """
        raise NotImplementedError("Subclasses must implement attach_data_feed_to_engine()")
