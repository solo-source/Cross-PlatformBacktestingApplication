import os
import sys
import pytest
from PySide6.QtWidgets import QTableWidgetItem
from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt
from src.gui.main_window import MainWindow
import pandas as pd
import backtrader as bt
import plotly.graph_objs as go

@pytest.fixture(autouse=True)
def qt_app(qtbot):
    """Ensure a QApplication exists."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    return app

def test_load_and_run_backtest(qtbot: QtBot, tmp_path):
    # Prepare a toy CSV
    csv = tmp_path / "test.csv"
    csv.write_text(
        "Date,Open,High,Low,Close,Volume\n" +
        "\n".join(f"2021-01-{i+1:02d},{100+i},{100+i},{100+i},{100+i},100" for i in range(30))
    )
    window = MainWindow()
    qtbot.addWidget(window)
    # Point CSV widget to our file
    window.csv_widget.df = pd.read_csv(str(csv), parse_dates=["Date"])
    window.csv_widget.data_rows = len(window.csv_widget.df)
    # Monkey-patch get_datafeed to use our df
    window.csv_widget.get_datafeed = lambda: [bt.feeds.PandasData(
        dataname=window.csv_widget.df.rename(columns={"Date":"datetime"}).set_index("datetime").assign(openinterest=0)
    )]
    # Run backtest
    qtbot.mouseClick(window.run_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: hasattr(window, 'last_pnl'), timeout=3000)
    assert window.last_pnl  # should exist

def test_export_report_creates_files(qtbot: QtBot, tmp_path, monkeypatch):
    # Reuse above setup
    from src.gui.main_window import MainWindow
    import backtrader as bt
    import pandas as pd

    # Prepare toy backtest data
    window = MainWindow()
    qtbot.addWidget(window)
    window.last_pnl = {1: 1000, 2: 1100}
    window.eq_plot = go.Figure()
    window.dd_plot = go.Figure()
    window.ret_plot = go.Figure()
    window.metrics_table.setRowCount(1)
    window.metrics_table.setItem(0, 0, QTableWidgetItem("Total Trades"))
    window.metrics_table.setItem(0, 1, QTableWidgetItem("1"))

    # Patch file dialog
    fake_pdf = str(tmp_path / "report.pdf")
    monkeypatch.setattr('src.gui.main_window.QFileDialog.getSaveFileName',
                        lambda *args, **kwargs: (fake_pdf, None))
    # Run export
    qtbot.mouseClick(window.export_button, Qt.LeftButton)
    # Assert PDF and CSV exist
    assert os.path.exists(fake_pdf)
    assert os.path.exists(fake_pdf.replace('.pdf', '_trades.csv'))
