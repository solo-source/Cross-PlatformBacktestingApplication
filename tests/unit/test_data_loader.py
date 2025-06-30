import pandas as pd
import backtrader as bt
import pytest
from src.data.loader import DataLoader

def test_from_csv(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text(
        "Date,Open,High,Low,Close,Volume\n"
        "2020-01-01,100,110,90,105,1000\n"
        "2020-01-02,106,112,104,110,1500\n"
    )
    feed, count = DataLoader.from_csv(str(csv))
    assert count == 2

    # Run a simple backtest to inspect data
    cerebro = bt.Cerebro()
    cerebro.adddata(feed)
    # create a do-nothing strategy
    cerebro.addstrategy(bt.Strategy)
    res = cerebro.run()[0]
    data0 = feed.lines
    # Check first and last close
    assert feed.close[0] == 105
    assert feed.close[-1] == 110

def test_from_csv_empty(tmp_path):
    csv = tmp_path / "empty.csv"
    csv.write_text("Date,Open,High,Low,Close,Volume\n")
    with pytest.raises(Exception):
        DataLoader.from_csv(str(csv))[0]

def test_from_yfinance(monkeypatch):
    # Mock yfinance
    import yfinance as yf
    df = pd.DataFrame({
        'Date': pd.to_datetime(['2021-01-01', '2021-01-02']),
        'Open': [200.0, 210.0],
        'High': [205.0, 215.0],
        'Low': [195.0, 205.0],
        'Close': [202.0, 212.0],
        'Volume': [10000, 15000]
    })
    monkeypatch.setattr(yf, 'download', lambda *args, **kwargs: df.set_index('Date'))
    feed = DataLoader.from_yfinance('FAKE', '2021-01-01', '2021-01-02')
    assert isinstance(feed, bt.feeds.PandasData)
    # Check dataname is DataFrame
    assert hasattr(feed.p, 'dataname')
