# src/gui/strategy_dialog.py
"""
StrategyDialog: let users build simple strategies via GUI.
"""

from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QPushButton

class StrategyDialog(QDialog):
    """Dialog to select predefined strategies and parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Strategy")
        form = QFormLayout(self)

        self.choice = QComboBox()
        self.choice.addItems(["SMA Crossover"])  # extend as needed
        form.addRow("Strategy:", self.choice)

        self.param1 = QSpinBox(); self.param1.setRange(1,200); self.param1.setValue(10)
        self.param2 = QSpinBox(); self.param2.setRange(1,500); self.param2.setValue(30)
        form.addRow("Param 1 (Short):", self.param1)
        form.addRow("Param 2 (Long):",  self.param2)

        btn = QPushButton("OK")
        btn.clicked.connect(self.accept)
        form.addRow(btn)

    def get_config(self):
        return {
            "strategy": self.choice.currentText(),
            "param1": self.param1.value(),
            "param2": self.param2.value()
        }
