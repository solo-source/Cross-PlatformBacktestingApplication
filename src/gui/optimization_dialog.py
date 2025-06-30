from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
import backtrader as bt
from src.gui.strategy_selector_widget import StrategySelectorWidget
from src.utils.logger import logger
import itertools


def _frange(start, stop, step):
    """Helper to generate float ranges inclusive."""
    vals = []
    x = start
    while x <= stop:
        vals.append(round(x, 8))
        x += step
    return vals


class OptimizationDialog(QDialog):
    """
    Dialog to configure and run parameter optimization for a selected strategy.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optimize Strategy Parameters")
        self.resize(600, 400)

        # Strategy selector
        self.strategy_widget = StrategySelectorWidget()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("Select Strategy and Parameter Ranges:"))
        self.layout.addWidget(self.strategy_widget)

        # Range form
        self.range_form = QFormLayout()
        self.layout.addLayout(self.range_form)
        self.param_ranges = {}
        self.strategy_widget.strategyChanged.connect(
            lambda name: self.build_range_inputs(name)
        )

        # Initial build
        self.build_range_inputs(self.strategy_widget.combo.currentText())

        # Run button
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Optimization")
        self.run_btn.clicked.connect(self.run_optimization)
        btn_layout.addWidget(self.run_btn)
        self.layout.addLayout(btn_layout)

        # Results table
        self.results_table = QTableWidget()
        self.layout.addWidget(self.results_table)

        # Data feeds placeholder
        self._feeds = []

    def set_datafeeds(self, feeds):
        """Supply the data feeds for optimization."""
        self._feeds = feeds
        # Grab the actual DataFrames so we can rebuild feeds later
        self._raw_dfs = [f.p.dataname.copy() for f in feeds]
        # Now rebuild the range inputs (so barcount is right)
        current = self.strategy_widget.combo.currentText()
        self.build_range_inputs(current)

    def build_range_inputs(self, name: str):
        # Clear old inputs
        while self.range_form.count():
            self.range_form.removeRow(0)

        # Determine available bars (fallback to a large number if called too early)
        if hasattr(self, '_feeds') and self._feeds:
            barcount = len(self._feeds[0].p.dataname)
        else:
            barcount = 9999

        # Load strategy specs
        _, specs = StrategySelectorWidget.STRATEGIES[name]
        self.param_ranges = {}

        for key, ptype, default, minimum, step, precision in specs:
            # Integer parameters
            if ptype is int:
                # “from” spinner: min .. (barcount-1)
                start = QSpinBox()
                start.setRange(minimum, max(minimum, barcount - 1))
                start.setValue(min(default, barcount - 1))

                # “to” spinner: min .. (barcount-1)
                end = QSpinBox()
                end.setRange(minimum, max(minimum, barcount - 1))
                end.setValue(min(default + step, barcount - 1))

                # step spinner: 1 .. (barcount-1)
                stepb = QSpinBox()
                stepb.setRange(1, max(1, barcount - 1))
                stepb.setValue(step)

            # Floating‑point parameters
            else:
                # “from” spinner
                start = QDoubleSpinBox()
                start.setDecimals(precision)
                start.setRange(minimum, float(max(minimum, barcount - 1)))
                start.setValue(min(default, barcount - 1))

                # “to” spinner
                end = QDoubleSpinBox()
                end.setDecimals(precision)
                end.setRange(minimum, float(max(minimum, barcount - 1)))
                end.setValue(min(default + step, barcount - 1))

                # step spinner
                stepb = QDoubleSpinBox()
                stepb.setDecimals(precision)
                stepb.setRange(step, float(max(step, barcount - 1)))
                stepb.setValue(step)

            # Add to form
            self.range_form.addRow(f"{key} from:", start)
            self.range_form.addRow(f"{key} to:", end)
            self.range_form.addRow(f"{key} step:", stepb)

            # Store references
            self.param_ranges[key] = (start, end, stepb)

    def run_optimization(self):
        try:
            strat_name = self.strategy_widget.combo.currentText()
            strat_cls, _ = StrategySelectorWidget.STRATEGIES[strat_name]

            # 1) Build the param grid
            grid = {
                key: _frange(start.value(), end.value(), step.value())
                for key, (start, end, step) in self.param_ranges.items()
            }
            names = list(grid.keys())
            values = [grid[n] for n in names]

            results = []

            # 2) Loop over every parameter combination
            for combo in itertools.product(*values):
                params = dict(zip(names, combo))

                # Optionally skip invalid combos (e.g. sma_short >= sma_long)
                if 'sma_short' in params and 'sma_long' in params:
                    if params['sma_short'] >= params['sma_long']:
                        continue

                try:
                    cerebro = bt.Cerebro()

                    # Re-create each feed exactly as the original
                    for df, orig_feed in zip(self._raw_dfs, self._feeds):
                        feed_kwargs = orig_feed.p._getkwargs().copy()
                        # Remove dataname so we can pass our df
                        feed_kwargs.pop('dataname', None)

                        feed = bt.feeds.PandasData(
                            dataname=df,
                            **feed_kwargs
                        )
                        cerebro.adddata(feed)

                    # Add the strategy with the current params
                    cerebro.addstrategy(strat_cls, **params)

                    # Run and collect result
                    runstrat = cerebro.run(maxcpus=1)[0]
                    final_val = round(runstrat.broker.getvalue(), 2)
                    results.append({**params, "FinalValue": final_val})

                except IndexError as ie:
                    # Skip combos that still require more bars than available
                    logger.warning(f"Skipping {params}: {ie}")
                    continue

            # 3) Display results
            if not results:
                QMessageBox.information(
                    self, "No Results",
                    "No parameter combinations could run to completion. "
                    "Ensure your data has at least as many rows as your longest look‑back."
                )
            else:
                self.show_results(results)

        except Exception as e:
            logger.exception("Optimization failed")
            QMessageBox.critical(self, "Optimization Error", str(e))

    def show_results(self, data: list):
        if not data:
            QMessageBox.information(self, "No Results", "No optimization results to show.")
            return

        headers = list(data[0].keys())
        self.results_table.clear()
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        self.results_table.setRowCount(len(data))

        for row_i, row in enumerate(data):
            for col_i, key in enumerate(headers):
                self.results_table.setItem(row_i, col_i, QTableWidgetItem(str(row[key])))

        self.results_table.resizeColumnsToContents()
