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
