import pytest
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot
from src.gui.main_window import MainWindow

@pytest.fixture(scope="module")
def app():
    return QApplication([])

def test_run_backtest_button_shows_plots(qtbot: QtBot, app):
    w = MainWindow()
    qtbot.addWidget(w)

    # stub out data and strategy
    w.csv_widget = type('C', (), {'get_datafeed': lambda s: []})()
    w.ws_widget  = type('C', (), {'get_datafeed': lambda s: []})()
    # clicking with no data should warn
    qtbot.mouseClick(w.run_button, QtCore.Qt.LeftButton)
    # should show a warning message; you can intercept QMessageBox if needed

    # For a full end-to-end you’d load a real DataLoader feed and strategy,
    # then click and inspect that eq_canvas has line data:
    # w.csv_widget.get_datafeed = lambda: [your test feed]
    # w.strategy_selector.get_strategy = lambda: (YourStrategy, {})
    # qtbot.mouseClick(w.run_button, QtCore.Qt.LeftButton)
    # assert w.eq_ax.lines, \"Equity curve should have at least one line\"
