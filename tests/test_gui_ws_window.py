import pytest
import pandas as pd
from PySide6.QtWidgets import QApplication
from src.gui.ws_window import WsBacktestWindow
import backtrader as bt

@pytest.fixture(scope="module")
def app():
    return QApplication([])

def test_ws_widget_csv_fallback(tmp_path, app, monkeypatch):
    # monkey-patch pandas.read_csv
    sample = pd.DataFrame({
        'Date': pd.date_range('2021-01-01', periods=5),
        'Open': [1,2,3,4,5], 'High':[1,2,3,4,5],
        'Low':[1,2,3,4,5], 'Close':[1,2,3,4,5], 'Volume':[10]*5
    })
    monkeypatch.setattr(pd, 'read_csv', lambda *args, **kw: sample)
    w = WsBacktestWindow()
    w.on_browse_csv()
    # now get_datafeed should work
    feeds = w.get_datafeed()
    assert isinstance(feeds, list) and isinstance(feeds[0], bt.feeds.PandasData)

def test_live_feed_toggle(monkeypatch, app):
    # simulate an empty download call
    import yfinance as yf
    monkeypatch.setattr(yf, 'download', lambda *args, **kw: pd.DataFrame())
    w = WsBacktestWindow()
    w.on_toggle_live()
    # since df is empty, rowcount remains 0
    assert w.data_rows == 0
    # toggle back off
    w.on_toggle_live()
    assert w.poll_timer is None
