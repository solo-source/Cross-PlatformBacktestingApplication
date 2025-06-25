# src/gui/data_source_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QRadioButton, QButtonGroup
from PySide6.QtCore import Signal

class DataSourceWidget(QWidget):
    OPTION_CSV = 'csv'
    OPTION_WS  = 'ws'

    sourceChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.radio_csv = QRadioButton("Load CSV File")
        self.radio_ws  = QRadioButton("Live WebSocket")
        self.radio_csv.setChecked(True)

        self.group = QButtonGroup(self)
        self.group.addButton(self.radio_csv)
        self.group.addButton(self.radio_ws)

        layout.addWidget(self.radio_csv)
        layout.addWidget(self.radio_ws)
        layout.addStretch()

        self.radio_csv.toggled.connect(self._emit_source)
        self.radio_ws.toggled.connect(self._emit_source)

    @property
    def current_source(self) -> str:
        return self.OPTION_CSV if self.radio_csv.isChecked() else self.OPTION_WS

    def _emit_source(self):
        self.sourceChanged.emit(self.current_source)