# src/gui/strategy_selector.py

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox
)
from src.backtester.strategies import (
    SmaWithTrailing, AtrPositionSizing,
    TimedExitSma, MultiTimeframeSma
)

# Explicit mapping: display name -> (strategy class, default params)
STRATEGIES = {
    "SMA + Trailing Stop": (
        SmaWithTrailing,
        {'fast': 10, 'slow': 30, 'trail_pct': 0.03}
    ),
    "ATR Position Sizing": (
        AtrPositionSizing,
        {'fast': 10, 'slow': 30, 'risk_perc': 0.01,
         'atr_period': 14, 'atr_mult': 3}
    ),
    "Timed-Exit SMA": (
        TimedExitSma,
        {'fast': 10, 'slow': 30, 'max_hold': 20}
    ),
    "Multi-Timeframe SMA": (
        MultiTimeframeSma,
        {'fast': 10, 'slow': 30}
    ),
}

class StrategySelectorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QFormLayout(self)

        # 1) Strategy dropdown
        self.combo = QComboBox()
        self.combo.addItems(STRATEGIES.keys())
        self.combo.currentTextChanged.connect(self._build_params)
        self.layout.addRow("Strategy:", self.combo)

        # 2) Parameter inputs container
        self.param_widgets = {}
        # Build inputs for the initially selected strategy
        self._build_params(self.combo.currentText())

    def _build_params(self, strategy_name):
        # Clear any old parameter widgets
        for widget in self.param_widgets.values():
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.param_widgets.clear()

        # Get defaults for the selected strategy
        _, defaults = STRATEGIES[strategy_name]

        # Create an input widget for each parameter
        for pname, pval in defaults.items():
            if isinstance(pval, int):
                box = QSpinBox()
                box.setRange(1, 10_000)
                box.setValue(pval)
            else:
                box = QDoubleSpinBox()
                # reasonable range for floats
                box.setRange(0.0, 1000.0)
                box.setDecimals(4)
                box.setValue(pval)
            self.param_widgets[pname] = box
            self.layout.addRow(f"{pname}:", box)

    def get_strategy(self):
        """
        Returns:
          strat_cls: the selected Strategy class
          params:    dict of {param_name: user_value}
        """
        name = self.combo.currentText()
        strat_cls, defaults = STRATEGIES[name]
        params = {
            pname: widget.value()
            for pname, widget in self.param_widgets.items()
        }
        return strat_cls, params
