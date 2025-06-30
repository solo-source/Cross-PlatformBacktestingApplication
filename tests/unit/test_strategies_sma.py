import pandas as pd
import backtrader as bt
import pytest
from src.backtester.strategies import SmaCross

class TestSmaCross:
    @pytest.fixture
    def simple_feed(self):
        # rising line: price = day index
        dates = pd.date_range("2021-01-01", periods=50, freq='D')
        df = pd.DataFrame({
            'datetime': dates,
            'Open': range(50),
            'High': range(50),
            'Low': range(50),
            'Close': range(50),
            'Volume': [100]*50,
            'openinterest': [0]*50
        }).set_index('datetime')
        return bt.feeds.PandasData(dataname=df)

    def test_single_crossover(self, simple_feed):
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(1000)
        cerebro.adddata(simple_feed)
        cerebro.addstrategy(SmaCross, sma_short=5, sma_long=10, printlog=False)
        res = cerebro.run()[0]
        # Expect at least one trade (short SMA crossing long)
        trades = res.analyzers.tradeanalyzer.get_analysis()
        total = trades.total.closed if hasattr(trades.total, 'closed') else 0
        assert total >= 1
        # Final value > starting cash
        assert res.broker.getvalue() >= 1000

    def test_no_trades_flat(self):
        # flat price → no crossover
        df = pd.DataFrame({
            'datetime': pd.date_range("2021-01-01", periods=20),
            'Open': [100]*20,
            'High': [100]*20,
            'Low': [100]*20,
            'Close': [100]*20,
            'Volume': [1]*20,
            'openinterest': [0]*20
        }).set_index('datetime')
        feed = bt.feeds.PandasData(dataname=df)
        cerebro = bt.Cerebro()
        cerebro.adddata(feed)
        cerebro.addstrategy(SmaCross, sma_short=2, sma_long=5, printlog=False)
        res = cerebro.run()[0]
        trades = res.analyzers.tradeanalyzer.get_analysis()
        total = trades.total.closed if hasattr(trades.total, 'closed') else 0
        assert total == 0
