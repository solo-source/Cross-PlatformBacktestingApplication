# src/backtester/engine.py
"""
BacktestEngine: wraps Backtrader Cerebro for running backtests.
Automatically adds a BuySell observer so that each buy/sell is printed to the console.
"""

import backtrader as bt


class BacktestEngine:
    """Engine to configure and run Backtrader backtests."""

    def __init__(self, cash: float = 100000.0, commission: float = 0.001):
        self.cerebro = bt.Cerebro()

        # Set initial cash and commission
        self.cerebro.broker.setcash(cash)
        self.cerebro.broker.setcommission(commission=commission)

        # Automatically attach BuySell observer to log buy/sell events
        self.cerebro.addobserver(bt.observers.BuySell)

    def add_data(self, data_feed: bt.feeds.PandasData):
        """
        Attach a historical or (simulated) live data feed.
        Example: a bt.feeds.PandasData instance.
        """
        self.cerebro.adddata(data_feed)

    def set_strategy(self, strat_cls: type, **params):
        """
        Add a strategy class with its parameters.
        Example: engine.set_strategy(SmaCross, sma_short=10, sma_long=30, printlog=True)
        """
        self.cerebro.addstrategy(strat_cls, **params)

    def add_observer(self, observer_cls, **kwargs):
        """
        Expose observer addition.
        Example: engine.add_observer(bt.observers.Trades)
        """
        self.cerebro.addobserver(observer_cls, **kwargs)

    def add_analyzer(self, analyzer_cls, **kwargs):
        """
        Expose analyzer addition.
        Example: engine.add_analyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        """
        self.cerebro.addanalyzer(analyzer_cls, **kwargs)

    def run(self):
        """
        Execute the backtest and return strategy instances.
        All buy/sell events will be printed via the BuySell observer.
        """
        return self.cerebro.run()
