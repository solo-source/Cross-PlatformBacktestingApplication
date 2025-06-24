# src/gui/data_source_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QRadioButton, QPushButton, QButtonGroup
)
from PySide6.QtCore import Qt


class DataSourceDialog(QDialog):
    """
    A simple dialog that asks the user to choose one of:
      1) CSV file
      2) REST Stream
      3) WebSocket Stream
    """

    OPTION_CSV = "csv"
    OPTION_REST = "rest"
    OPTION_WS  = "ws"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Data Feed")
        self.setModal(True)
        self.resize(300, 150)

        layout = QVBoxLayout(self)
        label = QLabel("Choose your data feed method:", self)
        layout.addWidget(label)

        # Create three radio buttons
        self.radio_csv = QRadioButton("1. Load CSV File", self)
        self.radio_rest = QRadioButton("2. REST Stream", self)
        self.radio_ws  = QRadioButton("3. WebSocket Stream", self)

        # By default, select CSV
        self.radio_csv.setChecked(True)

        # Add to a button group (so only one is selected)
        self.group = QButtonGroup(self)
        self.group.addButton(self.radio_csv)
        self.group.addButton(self.radio_rest)
        self.group.addButton(self.radio_ws)

        layout.addWidget(self.radio_csv)
        layout.addWidget(self.radio_rest)
        layout.addWidget(self.radio_ws)

        # “OK” button
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button, alignment=Qt.AlignRight)

    def selected_option(self) -> str:
        """
        Returns one of DataSourceDialog.OPTION_CSV, OPTION_REST, or OPTION_WS,
        corresponding to which radio button is checked.
        """
        if self.radio_csv.isChecked():
            return DataSourceDialog.OPTION_CSV
        elif self.radio_rest.isChecked():
            return DataSourceDialog.OPTION_REST
        elif self.radio_ws.isChecked():
            return DataSourceDialog.OPTION_WS
        return DataSourceDialog.OPTION_CSV
