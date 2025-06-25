# src/gui/main_window.py
import sys
import sqlite3
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

import backtrader as bt
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np
from PySide6.QtGui import QPixmap

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
        from src.gui.data_source_widget import DataSourceWidget
        from src.gui.strategy_selector_widget import StrategySelectorWidget
        from src.gui.csv_window import CsvBacktestWindow
        from src.gui.ws_window import WsBacktestWindow

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
        # scroll area for plots
        scroll = QScrollArea()
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        self._setup_plots(plot_layout)
        scroll.setWidget(plot_container)
        scroll.setWidgetResizable(True)
        results_layout.addWidget(scroll)
        tabs.addTab(results_tab, "Results")
        # Upload/History Tab
        upload_tab = QWidget()
        upload_layout = QVBoxLayout(upload_tab)
        form = QFormLayout()
        # inputs
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
        # buttons
        btn_layout = QHBoxLayout()
        self.upload_button = QPushButton("Save Snapshot")
        self.upload_button.clicked.connect(self._upload_snapshot)
        btn_layout.addWidget(self.upload_button)
        self.refresh_button = QPushButton("Refresh History")
        self.refresh_button.clicked.connect(self._load_history)
        btn_layout.addWidget(self.refresh_button)
        upload_layout.addLayout(btn_layout)
        # table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID','Symbol','Date','Title','Live'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self._on_table_click)
        upload_layout.addWidget(self.table)
        tabs.addTab(upload_tab, "Upload/History")

        splitter.addWidget(tabs)
        main_layout.addWidget(splitter)

        # Connect signals
        self.data_source_widget.sourceChanged.connect(self._on_source_changed)
        self.strategy_selector.strategyChanged.connect(lambda _: None)
        # run button moved inside ws/csv windows

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

    def _run_backtest(self):
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
        for fd in feeds:
            cerebro.adddata(fd)
        cerebro.addstrategy(strat_cls, **params)
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

        # 4) Run and collect results
        try:
            res = cerebro.run()[0]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backtest failed: {e}")
            return

        pnl = res.analyzers.returns.get_analysis()
        dd  = res.analyzers.drawdown.get_analysis()
        dates = list(pnl.keys())
        vals  = list(pnl.values())

        # 5) Plot Equity Curve
        self.eq_ax.clear()
        self.eq_ax.plot(dates, vals, marker='o')
        self.eq_ax.set_title('Equity Curve')
        self.eq_ax.set_xlabel('Date')
        self.eq_ax.set_ylabel('Portfolio Value')
        self.eq_canvas.draw()

        # 6) Plot Drawdown
        self.dd_ax.clear()
        self.dd_ax.plot(dd['drawdown'], marker='x')
        self.dd_ax.set_title('Drawdown')
        self.dd_ax.set_xlabel('Time')
        self.dd_ax.set_ylabel('Drawdown (%)')
        self.dd_canvas.draw()

        # 7) Plot Returns Distribution
        rets = np.diff(vals)
        self.ret_ax.clear()
        self.ret_ax.hist(rets, bins=30)
        self.ret_ax.set_title('Returns Distribution')
        self.ret_ax.set_xlabel('Returns')
        self.ret_ax.set_ylabel('Frequency')
        self.ret_canvas.draw()

        # Switch to Results tab
        try:
            # assuming tabs index 1 is Results
            self.centralWidget().findChild(QTabWidget).setCurrentIndex(1)
        except Exception:
            pass

    def _upload_snapshot(self):
        def to_blob(fig):
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=200)
            return buf.getvalue()

        eq_blob  = to_blob(self.eq_canvas.figure)
        dd_blob  = to_blob(self.dd_canvas.figure)
        hist_blob= to_blob(self.ret_canvas.figure)

        cur = self.conn.cursor()
        cur.execute(
            f"INSERT INTO {TABLE_NAME} (symbol, live, title, description, notes, date, equity_img, drawdown_img, histogram_img) VALUES (?,?,?,?,?,?,?,?,?)",
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