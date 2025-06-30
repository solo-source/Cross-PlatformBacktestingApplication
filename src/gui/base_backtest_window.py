# src/gui/base_backtest_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QVBoxLayout
)
from PySide6.QtCore import Qt
from src.backtester.engine import BacktestEngine
from src.utils.logger import logger

class BaseBacktestWindow(QMainWindow):
    """
    Base window that contains:
      - A "Load CSV" button to choose and load historical data
      - Initialization of BacktestEngine with loaded CSV feed
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modular Backtester")
        self.resize(1200, 800)

        self.engine = None
        self.data_rows = None
        self.csv_filepath = None

        # Central widget layout
        self._main = QWidget()
        self.setCentralWidget(self._main)
        h_layout = QHBoxLayout(self._main)

        # Left panel: Load CSV button
        self.load_button = QPushButton("Load CSV", self)
        self.load_button.clicked.connect(self.load_csv)
        h_layout.addWidget(self.load_button, alignment=Qt.AlignTop)

        # Right panel reserved for derived classes or further UI
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        h_layout.addWidget(self.content_area, stretch=1)

    def load_csv(self):
        """
        Open file dialog to select a CSV, load it via BacktestEngine,
        and set self.data_rows.
        """
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            self.csv_filepath = path
            # Initialize engine and load CSV feed
            self.engine = BacktestEngine()
            self.data_rows = self.engine.load_csv_feed(path)
            QMessageBox.information(
                self, "Success", f"Loaded {self.data_rows} rows from CSV.")
        except Exception as e:
            logger.exception("Failed to load CSV")
            QMessageBox.critical(self, "Error", f"Could not load CSV: {e}")
