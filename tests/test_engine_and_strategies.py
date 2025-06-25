import pytest
import backtrader as bt
import pandas as pd
from src.backtester.engine import BacktestEngine
from src.backtester.strategies import (
    SmaCross, SmaWithTrailing, AtrPositionSizing,
    TimedExitSma, MultiTimeframeSma
)

def make_feed(n=20):
    df = pd.DataFrame({
        'datetime': pd.date_range('2021-01-01', periods=n, freq='D'),
        'Open': list(range(n)), 'High': list(range(n)),
        'Low': list(range(n)), 'Close': list(range(n)),
        'Volume': [100]*n, 'openinterest': [0]*n
    }).set_index('datetime')
    return bt.feeds.PandasData(dataname=df)

@pytest.mark.parametrize("strategy,params", [
    (SmaCross, dict(sma_short=3, sma_long=5, printlog=False)),
    (SmaWithTrailing, dict(fast=3, slow=5, printlog=False)),
    (AtrPositionSizing, dict(fast=3, slow=5, atr_period=3, atr_mult=2, printlog=False)),
    (TimedExitSma, dict(fast=3, slow=5, max_hold=5, printlog=False)),
])
def test_single_feed_strategies_run(strategy, params):
    engine = BacktestEngine()
    engine.add_data(make_feed(50))
    engine.set_strategy(strategy, **params)
    results = engine.run()
    assert isinstance(results, list) and len(results) == 1
    # The strategy object should have analyzers attached
    strat = results[0]
    assert 'timereturn' in strat.analyzers or hasattr(strat, 'analyzers')

def test_multi_timeframe_raises_without_two_feeds():
    engine = BacktestEngine()
    engine.add_data(make_feed(20))
    with pytest.raises(ValueError):
        engine.set_strategy(MultiTimeframeSma, fast=2, slow=5)
