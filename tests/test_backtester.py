# tests/test_backtester.py
"""
Basic tests for DataLoader and SMA strategy execution.
"""

import pytest
import backtrader as bt
import pandas as pd
from src.data.loader import DataLoader
from src.backtester.engine import BacktestEngine
from src.backtester.strategies import SmaCross

def test_csv_loader(tmp_path):
    # create dummy CSV
    df = pd.DataFrame({
        'Date': pd.date_range('2021-01-01', periods=5),
        'Open': [1,2,3,4,5],
        'High': [1,2,3,4,5],
        'Low':  [1,2,3,4,5],
        'Close':[1,2,3,4,5],
        'Volume':[100,100,100,100,100]
    })
    file = tmp_path / "data.csv"
    df.to_csv(file, index=False)
    feed = DataLoader.from_csv(str(file))
    assert isinstance(feed, bt.feeds.GenericCSVData)

def test_sma_strategy_runs():
    # synthetic feed
    df = pd.DataFrame({
        'Date': pd.date_range('2021-01-01', periods=10),
        'Open': list(range(1,11)),
        'High': list(range(1,11)),
        'Low':  list(range(1,11)),
        'Close':list(range(1,11)),
        'Volume':[100]*10
    })
    feed = bt.feeds.PandasData(dataname=df.set_index('Date'))
    engine = BacktestEngine()
    engine.add_data(feed)
    engine.set_strategy(SmaCross, sma_short=2, sma_long=5)
    results = engine.run()
    assert results  # ran without error
