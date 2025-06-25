# src/gui/strategy_selector_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QFormLayout, QLabel,
    QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Signal

# Import your actual strategy classes
from src.backtester.strategies import (
    SmaCross, SmaWithTrailing, AtrPositionSizing,
    TimedExitSma, MultiTimeframeSma
)

class StrategySelectorWidget(QWidget):
    strategyChanged = Signal(str)

    # Map display names to (class, parameter specs)
    # Each param spec: (param_key, type, default, min, step, precision)
    STRATEGIES = {
        'SMA Crossover': (
            SmaCross,
            [
                ('sma_short', int,    10,   1,   1, 0),
                ('sma_long',  int,    30,   1,   1, 0),
                ('stop_loss_pct',   float, 0.02, 0.01,0.01,2),
                ('take_profit_pct', float, 0.05, 0.01,0.01,2),
                ('risk_per_trade_pct', float,0.01,0.01,0.01,2)
            ]
        ),
        'SMA with Trailing': (
            SmaWithTrailing,
            [
                ('fast',    int,    10,   1,   1, 0),
                ('slow',    int,    30,   1,   1, 0),
                ('trail_pct', float, 0.03, 0.01,0.01,2)
            ]
        ),
        'ATR Position Sizing': (
            AtrPositionSizing,
            [
                ('fast',       int,    10,   1,   1, 0),
                ('slow',       int,    30,   1,   1, 0),
                ('atr_period', int,    14,   1,   1, 0),
                ('atr_mult',   float,  3.0,  0.1, 0.1,1),
                ('risk_perc',  float,  0.01, 0.01,0.01,2)
            ]
        ),
        'Timed Exit SMA': (
            TimedExitSma,
            [
                ('fast',    int,    10,   1,   1, 0),
                ('slow',    int,    30,   1,   1, 0),
                ('max_hold',int,    20,   1,   1, 0)
            ]
        ),
        'Multi Timeframe SMA': (
            MultiTimeframeSma,
            [
                ('fast',    int,    10,   1,   1, 0),
                ('slow',    int,    30,   1,   1, 0)
            ]
        )
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.combo = QComboBox()
        self.combo.addItems(self.STRATEGIES.keys())
        layout.addWidget(QLabel("Select Strategy:"))
        layout.addWidget(self.combo)

        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        layout.addWidget(self.form_widget)

        # Build initial form
        self._build_form(self.combo.currentText())

        self.combo.currentTextChanged.connect(self._on_strategy_change)

    def _on_strategy_change(self, name: str):
        self._build_form(name)
        self.strategyChanged.emit(name)

    def _build_form(self, name: str):
        # Clear old widgets
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.inputs = {}
        cls, specs = self.STRATEGIES[name]
        for key, ptype, default, minimum, step, precision in specs:
            label = key.replace('_', ' ').title()
            if ptype is int:
                spin = QSpinBox()
                spin.setRange(minimum, 9999)
                spin.setSingleStep(step)
                spin.setValue(default)
                self.form_layout.addRow(f"{label}:", spin)
                self.inputs[key] = spin
            else:
                dspin = QDoubleSpinBox()
                dspin.setRange(minimum, 100.0)
                dspin.setSingleStep(step)
                dspin.setDecimals(precision)
                dspin.setValue(default)
                self.form_layout.addRow(f"{label}:", dspin)
                self.inputs[key] = dspin

    def get_parameters(self) -> dict:
        return {key: widget.value() for key, widget in self.inputs.items()}

    def     get_strategy(self):
        """
        Returns (strategy_class, parameters_dict).
        """
        name = self.combo.currentText()
        cls, _ = self.STRATEGIES[name]
        params = self.get_parameters()
        return cls, params