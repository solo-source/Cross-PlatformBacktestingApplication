import pandas as pd
import backtrader as bt
import pytest
from src.data.loader import DataLoader
from src.backtester.strategies import SmaCross


def test_full_pipeline(tmp_path):
    # Create a toy CSV with one upward crossover
    csv = tmp_path / "toy.csv"
    prices = list(range(20))
    df = pd.DataFrame({
        'Date': pd.date_range("2021-01-01", periods=20),
        'Open': prices,
        'High': prices,
        'Low': prices,
        'Close': prices,
        'Volume': [10] * 20
    })
    df.to_csv(csv, index=False)

    feed, rows = DataLoader.from_csv(str(csv))
    assert rows == 20

    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000)
    cerebro.adddata(feed)
    cerebro.addstrategy(SmaCross, sma_short=3, sma_long=5, printlog=False)
    res = cerebro.run()[0]
    # Check final portfolio value directly (no analyzers added)
    final_value = res.broker.getvalue()
    assert final_value >= 1000
