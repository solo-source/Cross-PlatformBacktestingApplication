import pandas as pd
import backtrader as bt
import pytest
from src.backtester.strategies import SmaCross

def generate_stop_series():
    # price jumps down after entry to trigger stop-loss
    prices = [10]*10 + [9]*10
    dates = pd.date_range("2022-01-01", periods=len(prices))
    df = pd.DataFrame({
        'datetime': dates,
        'Open': prices,
        'High': prices,
        'Low': prices,
        'Close': prices,
        'Volume': [1]*len(prices),
        'openinterest': [0]*len(prices)
    }).set_index('datetime')
    return bt.feeds.PandasData(dataname=df)

def test_stop_loss_triggers():
    feed = generate_stop_series()
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000)
    # very tight stop-loss
    cerebro.adddata(feed)
    cerebro.addstrategy(SmaCross,
                        sma_short=2,
                        sma_long=3,
                        stop_loss_pct=0.01,
                        take_profit_pct=0.10,
                        risk_per_trade_pct=0.1,
                        printlog=False)
    res = cerebro.run()[0]
    trades = res.analyzers.tradeanalyzer.get_analysis()
    total = trades.total.closed if hasattr(trades.total, 'closed') else 0
    assert total >= 1
    # ensure some trades lost money
    profits = [t['profit'] for t in trades.trades.values()] if hasattr(trades, 'trades') else []
    assert any(p < 0 for p in profits)
