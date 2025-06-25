import pandas as pd
import pytest
import backtrader as bt
from src.data.loader import DataLoader

def make_csv(tmp_path):
    df = pd.DataFrame({
        'Date': pd.date_range('2021-01-01', periods=5),
        'Open': [1,2,3,4,5],
        'High': [1,2,3,4,5],
        'Low':  [1,2,3,4,5],
        'Close':[1,2,3,4,5],
        'Volume':[10,20,30,40,50]
    })
    path = tmp_path / "test.csv"
    df.to_csv(path, index=False)
    return str(path), df

def test_from_csv_returns_feed(tmp_path):
    path, df = make_csv(tmp_path)
    feed = DataLoader.from_csv(path)
    assert isinstance(feed, bt.feeds.GenericCSVData)
    # spot-check: first close price matches
    assert feed.lines.close[0] == df.Close.iloc[0]

def test_from_yfinance_returns_feed(monkeypatch):
    class DummyDF:
        def __init__(self):
            self._data = pd.DataFrame({
                'Open': [100], 'High': [110], 'Low': [90], 'Close': [105], 'Volume': [1000]
            }, index=pd.DatetimeIndex(['2021-01-01']))
        def reset_index(self): return self._data.reset_index()
    monkeypatch.setattr(DataLoader, "_download_yf", lambda s, **kw: DummyDF())
    feed = DataLoader.from_yfinance("FAKE", "2021-01-01", "2021-01-02")
    assert hasattr(feed, 'lines')
    assert feed.lines.close[0] == 105
