# src/gui/main_window.py
import sys
import sqlite3
import os
from datetime import datetime
from io import BytesIO

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QTabWidget, QPushButton, QLineEdit, QTextEdit,
    QLabel, QCheckBox, QDateEdit, QFormLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QHBoxLayout, QVBoxLayout, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView
from src.gui.report_generator import ReportGenerator
from PySide6.QtWidgets import QPushButton, QFileDialog

from PySide6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objs as go
from plotly.subplots import make_subplots

import backtrader as bt
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np
from PySide6.QtGui import QPixmap
from src.gui.optimization_dialog import OptimizationDialog
from src.gui.data_source_widget import DataSourceWidget
from src.gui.strategy_selector_widget import StrategySelectorWidget
from src.gui.csv_window import CsvBacktestWindow
from src.gui.ws_window import WsBacktestWindow

# --- BEGIN MONKEY-PATCH FOR BACKTRADER ---
# This is a global fix for older backtrader versions where PandasData
# objects are created without the necessary '_tz' attribute.

# 1. Store the original __init__ method
_original_pandas_data_init = bt.feeds.PandasData.__init__


def _patched_pandas_data_init(self, *args, **kwargs):
    """A new __init__ that calls the original and then fixes the object."""
    # 2. Call the original __init__ to let it do its work
    _original_pandas_data_init(self, *args, **kwargs)

    # 3. After initialization, forcefully ensure '_tz' exists.
    #    It checks if a 'tz' parameter was passed, otherwise defaults to None.
    self._tz = getattr(self.p, 'tz', None)

    # Fix _calendar to avoid attribute errors in optimization
    if not hasattr(self, '_calendar'):
        self._calendar = None
    if not hasattr(self, 'fromdate'):
        self.fromdate = None
    if not hasattr(self, 'todate'):
        self.todate = None

    self.sessionstart = getattr(self, 'sessionstart', None)
    self.sessionend = getattr(self, 'sessionend', None)
# 4. Replace the original __init__ with our patched version
bt.feeds.PandasData.__init__ = _patched_pandas_data_init

# --- END MONKEY-PATCH FOR BACKTRADER ---


# SQLite database file
DB_PATH = 'snapshots.db'
TABLE_NAME = 'snapshots'

class ImagePreviewDialog(QDialog):
    def __init__(self, eq_blob, dd_blob, hist_blob, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Snapshot Preview")
        # allow interaction
        scroll = QScrollArea(self)
        container = QWidget()
        layout = QHBoxLayout(container)
        for blob, title in [(eq_blob, 'Equity'), (dd_blob, 'Drawdown'), (hist_blob, 'Histogram')]:
            pix = QPixmap()
            pix.loadFromData(blob)
            label = QLabel()
            label.setPixmap(pix.scaled(1920, 1080, Qt.KeepAspectRatio))
            sub = QVBoxLayout()
            sub.addWidget(QLabel(title))
            sub.addWidget(label)
            wrapper = QWidget()
            wrapper.setLayout(sub)
            layout.addWidget(wrapper)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        main = QVBoxLayout(self)
        main.addWidget(scroll)
        self.resize(820, 620)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modular Backtester")
        self._init_db()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        splitter = QSplitter(Qt.Horizontal)
        # Left Tools Panel
        tools_panel = QWidget()
        tools_layout = QVBoxLayout(tools_panel)

        self.data_source_widget = DataSourceWidget()
        tools_layout.addWidget(self.data_source_widget)
        self.strategy_selector = StrategySelectorWidget()
        tools_layout.addWidget(self.strategy_selector)
        # Run Backtest button
        self.run_button = QPushButton("Run Backtest")
        self.run_button.clicked.connect(self._run_backtest)
        tools_layout.addWidget(self.run_button)
        tools_layout.addStretch()
        splitter.addWidget(tools_panel)

        # Optimize button
        self.optimize_button = QPushButton("Optimize Strategy")
        self.optimize_button.clicked.connect(self._open_optimization_dialog)
        tools_layout.addWidget(self.optimize_button)
        tools_layout.addStretch()

        #export report button
        self.export_button = QPushButton("Export Report")
        self.export_button.clicked.connect(self._export_report)
        tools_layout.addWidget(self.export_button)

        # Right Tabs
        tabs = QTabWidget()
        # Data Tab
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        self.csv_widget = CsvBacktestWindow()
        data_layout.addWidget(self.csv_widget)
        self.ws_widget = WsBacktestWindow()
        data_layout.addWidget(self.ws_widget)
        tabs.addTab(data_tab, "Data")

        # Results Tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        # Plotly view for interactive charts
        self.plotly_view = QWebEngineView()
        results_layout.addWidget(self.plotly_view)
        tabs.addTab(results_tab, "Results")

        # Metrics Tab
        metrics_tab = QWidget()
        metrics_layout = QVBoxLayout(metrics_tab)
        self.metrics_table = QTableWidget(0, 2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.metrics_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.metrics_table.setMinimumHeight(200)
        metrics_layout.addWidget(self.metrics_table)
        tabs.addTab(metrics_tab, "Metrics")

        # Upload/History Tab
        upload_tab = QWidget()
        upload_layout = QVBoxLayout(upload_tab)
        form = QFormLayout()
        self.symbol_input = QLineEdit()
        form.addRow("Symbol:", self.symbol_input)
        self.live_checkbox = QCheckBox()
        form.addRow("Live:", self.live_checkbox)
        self.title_input = QLineEdit()
        form.addRow("Title:", self.title_input)
        self.desc_input = QLineEdit()
        form.addRow("Description:", self.desc_input)
        self.notes_input = QTextEdit()
        form.addRow("Notes:", self.notes_input)
        self.date_input = QDateEdit()
        self.date_input.setDate(datetime.now())
        self.date_input.setDisplayFormat('yyyy-MM-dd')
        form.addRow("Date:", self.date_input)
        upload_layout.addLayout(form)
        btn_layout = QHBoxLayout()
        self.upload_button = QPushButton("Save Snapshot")
        self.upload_button.clicked.connect(self._upload_snapshot)
        btn_layout.addWidget(self.upload_button)
        self.refresh_button = QPushButton("Refresh History")
        self.refresh_button.clicked.connect(self._load_history)
        btn_layout.addWidget(self.refresh_button)
        upload_layout.addLayout(btn_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'Symbol', 'Date', 'Title', 'Live'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self._on_table_click)
        upload_layout.addWidget(self.table)
        tabs.addTab(upload_tab, "Upload/History")

        splitter.addWidget(tabs)
        main_layout.addWidget(splitter)


        # Connect signals
        self.data_source_widget.sourceChanged.connect(self._on_source_changed)
        self.strategy_selector.strategyChanged.connect(lambda _: None)

        # Initialize
        self._on_source_changed(self.data_source_widget.current_source)
        self._load_history()

    def _init_db(self):
        self.conn = sqlite3.connect(DB_PATH)
        cur = self.conn.cursor()
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                live INTEGER,
                title TEXT,
                description TEXT,
                notes TEXT,
                date TEXT,
                equity_img BLOB,
                drawdown_img BLOB,
                histogram_img BLOB
            )
            """
        )
        self.conn.commit()
        cur.close()

    def _setup_plots(self, layout):
        def make_canvas(title, ax_setup, xlabel, ylabel):
            layout.addWidget(QLabel(title))
            canvas = FigureCanvas(Figure(figsize=(8, 4)))
            toolbar = NavigationToolbar(canvas, self)
            layout.addWidget(canvas)
            layout.addWidget(toolbar)
            ax = canvas.figure.subplots()
            ax_setup(ax)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            canvas.mpl_connect('pick_event', self._on_pick)
            return canvas, ax

        eq_setup = lambda ax: ax.grid(True)
        self.eq_canvas, self.eq_ax = make_canvas(
            "Equity Curve", eq_setup, "Date", "Portfolio Value"
        )
        dd_setup = lambda ax: ax.grid(True)
        self.dd_canvas, self.dd_ax = make_canvas(
            "Drawdown", dd_setup, "Time", "Drawdown (%)"
        )
        hist_setup = lambda ax: ax.grid(True)
        self.ret_canvas, self.ret_ax = make_canvas(
            "Returns Distribution", hist_setup, "Returns", "Frequency"
        )

    def _on_source_changed(self, source):
        self.csv_widget.setVisible(source == self.data_source_widget.OPTION_CSV)
        self.ws_widget.setVisible(source == self.data_source_widget.OPTION_WS)

    def _open_optimization_dialog(self):
        # collect the exact same feed used in the normal backtest
        if self.data_source_widget.current_source == self.data_source_widget.OPTION_CSV:
            feeds = self.csv_widget.get_datafeed()
        else:
            feeds = self.ws_widget.get_datafeed()

        #Instantiate and then pass them along.
        dlg = OptimizationDialog(self)
        dlg.set_datafeeds(feeds)

        #show the dialog
        dlg.exec_()

    def _run_backtest(self):
        self.last_pnl = {}
        self.last_trade_analysis = None
        """
        Launches the backtest using the selected data source and strategy,
        then plots results in the Results tab.
        """
        # 1) Retrieve strategy and params
        try:
            strat_cls, params = self.strategy_selector.get_strategy()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Strategy selection failed: {e}")
            return

        # 2) Get data feeds
        try:
            if self.data_source_widget.current_source == self.data_source_widget.OPTION_CSV:
                feeds = self.csv_widget.get_datafeed()
            else:
                feeds = self.ws_widget.get_datafeed()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Data feed error: {e}")
            return

        # 3) Setup Cerebro
        cerebro = bt.Cerebro()
        print("RUNNING BACKTEST WITH FEEDS:", feeds)
        for fd in feeds:
            cerebro.adddata(fd)
        cerebro.addstrategy(strat_cls, **params)
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade')
        # 4) Run and collect results
        try:
            res = cerebro.run()[0]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backtest failed: {e}")
            return

        pnl = res.analyzers.returns.get_analysis()
        # --- BEGIN FALLBACK FOR EMPTY PNL ---
        if not pnl:
            # No return series (e.g. flat data) → use starting and ending cash
            start_cash = cerebro.broker.startingcash if hasattr(cerebro.broker,'startingcash') else cerebro.broker.getcash()
            end_cash = res.broker.getvalue()
            pnl = {0: start_cash, 1: end_cash}
        # --- END FALLBACK ---
        self.last_pnl = pnl
        dd  = res.analyzers.drawdown.get_analysis()
        ta = res.analyzers.trade.get_analysis()
        self.last_trade_analysis = res.analyzers.trade.get_analysis()

        # dates = list(pnl.keys())
        # vals  = list(pnl.values())

        # Prepare series
        dates = list(pnl.keys())
        equity_vals = np.array(list(pnl.values()))
        # Safe drawdown calculation: avoid divide-by-zero
        cummax = np.maximum.accumulate(equity_vals)
        drawdown_pct = np.where(cummax > 0, (equity_vals - cummax) / cummax * 100, 0)

        # Returns series and rolling metrics
        returns = np.diff(equity_vals)
        rolling_sharpe = []
        window = 20  # 20-period rolling
        for i in range(len(returns)):
            if i < window:
                rolling_sharpe.append(None)
            else:
                rw = returns[i - window + 1:i + 1]
                sr = (np.mean(rw) / np.std(rw, ddof=1)) * np.sqrt(window) if np.std(rw, ddof=1) != 0 else 0
                rolling_sharpe.append(sr)
        # pad to full length
        rolling_sharpe = [None] + rolling_sharpe  # align length with dates

        # Build a 2x2 dashboard: equity, drawdown, returns hist, rolling Sharpe
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Equity Curve', 'Drawdown (%)', 'Returns Distribution', 'Rolling Sharpe'),
            vertical_spacing=0.2, horizontal_spacing=0.1
        )
        # Equity Curve
        fig.add_trace(go.Scatter(x=dates, y=equity_vals, mode='lines', name='Equity'), row=1, col=1)
        # Drawdown
        fig.add_trace(go.Bar(x=dates, y=drawdown_pct, name='Drawdown'), row=1, col=2)
        # Returns Histogram
        fig.add_trace(go.Histogram(x=returns, nbinsx=30, name='Returns'), row=2, col=1)
        # Rolling Sharpe
        fig.add_trace(go.Scatter(x=dates, y=rolling_sharpe, mode='lines', name='Rolling Sharpe'), row=2, col=2)

        fig.update_layout(
            title='Backtest Performance Dashboard',
            height=800, width=1200,
            showlegend=False
        )

        # Render and display
        html_str = fig.to_html(include_plotlyjs='cdn')
        self.plotly_view.setHtml(html_str)

        self.eq_plot = go.Figure(go.Scatter(x=dates, y=equity_vals, mode='lines'))
        self.dd_plot = go.Figure(go.Bar(x=dates, y=drawdown_pct))
        self.ret_plot = go.Figure(go.Histogram(x=np.diff(equity_vals), nbinsx=30))


        # Compute metrics
        total_trades = getattr(getattr(ta, 'total', {}), 'closed', 0)
        wins = getattr(getattr(ta, 'won', {}), 'total', 0)
        losses = getattr(getattr(ta, 'lost', {}), 'total', 0)
        win_rate = (wins / total_trades * 100) if total_trades else 0
        # Gather per-trade durations and profits if available
        hold_times = []
        profits = []
        try:
            trades = ta.trades  # may KeyError if not present
        except KeyError:
            trades = {}
        for t in trades.values():
            hold_times.append(t.get('duration', 0))
            profits.append(t.get('profit', 0))
        avg_hold = (sum(hold_times) / len(hold_times)) if hold_times else 0
        # average profit/loss
        avg_profit = (sum(p for p in profits if p > 0) / wins) if wins else 0
        avg_loss = (sum(p for p in profits if p < 0) / losses) if losses else 0
        # expectancy = win_rate% * avg_profit + loss_rate% * avg_loss
        expectancy = ((wins / total_trades) * avg_profit + (losses / total_trades) * avg_loss) if total_trades else 0

        # max consecutive losses
        def get_attr_safe(obj, name):
            try:
                return getattr(obj, name)
            except Exception:
                return 0

        max_consec_loss = get_attr_safe(getattr(ta, 'streak', {}), 'down')

        # 4. Populate metrics table:
        # ---------------------------
        self.metrics_table.setRowCount(0)
        metrics = [
            ("Total Trades", total_trades),
            ("Winning Trades", wins),
            ("Losing Trades", losses),
            ("Win Rate (%)", f"{win_rate:.2f}"),
            ("Avg Hold Time (bars)", f"{avg_hold:.1f}"),
            ("Expectancy", f"{expectancy:.2f}"),
            ("Max Consecutive Losses", max_consec_loss)
        ]
        for i, (label, value) in enumerate(metrics):
            self.metrics_table.insertRow(i)
            self.metrics_table.setItem(i, 0, QTableWidgetItem(str(label)))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(str(value)))
        self.metrics_table.resizeColumnsToContents()

        # Switch to Results tab
        try:
            # assuming tabs index 1 is Results
            self.centralWidget().findChild(QTabWidget).setCurrentIndex(1)
        except Exception:
            pass

    def _export_report(self):
        """
        Gather the latest backtest data (equity, drawdown, returns, metrics, trades) and generate HTML and PDF reports.
        """
        # Ensure we have run results
        if not hasattr(self, 'last_pnl') or not self.last_pnl:
            QMessageBox.warning(self, "No Data", "Run a backtest before exporting a report.")
            return

        # Prepare series
        dates = list(self.last_pnl.keys())
        equity_vals = list(self.last_pnl.values())

        # Drawdown and returns
        import numpy as np
        equity_arr = np.array(equity_vals)
        cummax = np.maximum.accumulate(equity_arr)
        drawdown_pct = np.where(cummax > 0,
                                (equity_arr - cummax) / cummax * 100,
                                0).tolist()
        returns = np.diff(equity_arr).tolist()

        # Trade metrics and log
        ta = getattr(self, 'last_trade_analysis', None)
        metrics = {}
        trades_table = []
        if ta:
            total = getattr(getattr(ta, 'total', {}), 'closed', 0)
            won = getattr(getattr(ta, 'won', {}), 'total', 0)
            lost = getattr(getattr(ta, 'lost', {}), 'total', 0)
            win_rate = (won / total * 100) if total else 0
            metrics = {
                'Total Trades': total,
                'Winning Trades': won,
                'Losing Trades': lost,
                'Win Rate (%)': f"{win_rate:.2f}"
            }
            try:
                trades_dict = ta.trades
            except KeyError:
                trades_dict = {}
            for tradeid, t in trades_dict.items():
                entry = t.get('entrybar', '')
                exit_ = t.get('exitbar', '')
                profit = t.get('profit', 0)
                duration = t.get('duration', 0)
                trades_table.append({
                    'Trade ID': tradeid,
                    'Entry Bar': entry,
                    'Exit Bar': exit_,
                    'Profit': profit,
                    'Duration': duration
                })
        else:
            metrics = {self.metrics_table.item(i, 0).text(): self.metrics_table.item(i, 1).text()
                       for i in range(self.metrics_table.rowCount())}

        # Ask user where to save
        pdf_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "PDF Files (*.pdf)")
        if not pdf_path:
            return
        if not pdf_path.lower().endswith('.pdf'):
            pdf_path += '.pdf'

        # Generate embedded Plotly divs from stored figures
        equity_div = self.eq_plot.to_html(full_html=False, include_plotlyjs='cdn') if hasattr(self,
                                                                                              'eq_plot') else "<p>No Equity Chart</p>"
        drawdown_div = self.dd_plot.to_html(full_html=False, include_plotlyjs='cdn') if hasattr(self,
                                                                                                'dd_plot') else "<p>No Drawdown Chart</p>"
        returns_div = self.ret_plot.to_html(full_html=False, include_plotlyjs='cdn') if hasattr(self,
                                                                                                'ret_plot') else "<p>No Returns Chart</p>"

        # Build context for report
        context = {
            'title': f"Backtest Report: {self.title_input.text()}",
            'date': self.date_input.date().toString('yyyy-MM-dd'),
            'equity_div': equity_div,
            'drawdown_div': drawdown_div,
            'returns_div': returns_div,
            'metrics': metrics,
            'trades_table': trades_table,
            'final_value': f"{equity_vals[-1]:.2f}",
            'max_drawdown': f"{min(drawdown_pct):.2f}%",
            'cagr': (lambda ev: f"{(((ev[-1]/ev[0])**(1/(len(ev)-1))) - 1)*100:.2f}%" if len(ev)>1 and ev[0]!=0 else "0.00%")(equity_vals)
        }

        # Generate and save report
        rg = ReportGenerator(template_dir=os.path.join(os.path.dirname(__file__), '../../templates'))
        try:
            html_file, pdf_file = rg.generate_report(context, output_dir=os.getcwd(),
                                                     filename=os.path.basename(pdf_path))
            QMessageBox.information(self, 'Report Saved', f"Report saved as:{pdf_file}")

            # # Optional: export CSV of trades
            # if trades_table:
            #     import csv
            # csv_path = pdf_path.replace('.pdf', '_trades.csv')
            # with open(csv_path, 'w', newline='') as f:
            #     writer = csv.DictWriter(f, fieldnames=trades_table[0].keys())
            # writer.writeheader()
            # writer.writerows(trades_table)
        except Exception as e:
            QMessageBox.critical(self, 'Export Error', str(e))

    def _upload_snapshot(self):
        """
        Capture the last run’s charts (equity, drawdown, returns) via Plotly
        and save them to the SQLite database as PNG blobs.
        """
        import numpy as np
        import plotly.graph_objs as go
        import plotly.io as pio
        from io import BytesIO

        # 1) Validate that we've run a backtest and have PnL
        if not hasattr(self, 'last_pnl') or not self.last_pnl:
            QMessageBox.warning(self, "No Backtest", "Please run a backtest before saving a snapshot.")
            return

        # 2) Prepare series
        dates = list(self.last_pnl.keys())
        equity_vals = np.array(list(self.last_pnl.values()))

        # Drawdown series (%)
        cummax = np.maximum.accumulate(equity_vals)
        drawdown_pct = np.where(cummax > 0,
                                (equity_vals - cummax) / cummax * 100,
                                0)

        # Returns series
        returns = np.diff(equity_vals)

        # 3) Build Plotly figures
        # 3.1 Equity Curve
        eq_fig = go.Figure(go.Scatter(
            x=dates, y=equity_vals, mode='lines', name='Equity'
        ))
        eq_fig.update_layout(
            title='Equity Curve',
            xaxis_title='Date',
            yaxis_title='Portfolio Value'
        )

        # 3.2 Drawdown
        dd_fig = go.Figure(go.Bar(
            x=dates, y=drawdown_pct.tolist(), name='Drawdown'
        ))
        dd_fig.update_layout(
            title='Drawdown (%)',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)'
        )

        # 3.3 Returns Distribution
        hist_fig = go.Figure(go.Histogram(
            x=returns, nbinsx=30, name='Returns'
        ))
        hist_fig.update_layout(
            title='Returns Distribution',
            xaxis_title='Returns',
            yaxis_title='Frequency'
        )

        # 4) Convert figures to PNG blobs via Kaleido
        #    Requires `pip install kaleido`
        eq_blob   = pio.to_image(eq_fig, format='png', width=1080, height=700, scale=2)
        dd_blob   = pio.to_image(dd_fig, format='png', width=1080, height=700, scale=2)
        hist_blob = pio.to_image(hist_fig, format='png', width=1080, height=700, scale=2)

        # 5) Write to SQLite
        cur = self.conn.cursor()
        cur.execute(
            f"INSERT INTO {TABLE_NAME} "
            "(symbol, live, title, description, notes, date, equity_img, drawdown_img, histogram_img) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                self.symbol_input.text(),
                int(self.live_checkbox.isChecked()),
                self.title_input.text(),
                self.desc_input.text(),
                self.notes_input.toPlainText(),
                self.date_input.date().toString('yyyy-MM-dd'),
                eq_blob, dd_blob, hist_blob
            )
        )
        self.conn.commit()
        cur.close()

        QMessageBox.information(self, 'Saved', 'Snapshot saved to database.')
        self._load_history()

    def _load_history(self):
        cur = self.conn.cursor()
        cur.execute(f"SELECT id, symbol, date, title, live FROM {TABLE_NAME} ORDER BY date DESC")
        rows = cur.fetchall()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        cur.close()

    def _on_table_click(self, row, col):
        cur = self.conn.cursor()
        snapshot_id = int(self.table.item(row, 0).text())
        cur.execute(f"SELECT equity_img, drawdown_img, histogram_img FROM {TABLE_NAME} WHERE id = ?", (snapshot_id,))
        eq, dd, hist = cur.fetchone()
        cur.close()
        dlg = ImagePreviewDialog(eq, dd, hist, self)
        dlg.exec()

    def _on_pick(self, event):
        """
        Handler for matplotlib pick events; currently no-op.
        """
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())