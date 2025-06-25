# src/backtester/strategies.py
"""
Predefined Backtrader strategies, including SMA crossover with risk controls,
trailing stops, ATR-based sizing, timed exits, and multi-timeframe logic.
Each strategy now supports `printlog=True` to output buy/sell events to the console.
"""

import backtrader as bt
import datetime


class SmaCross(bt.Strategy):
    """
    Simple Moving Average Crossover Strategy with built-in stop-loss / take-profit
    and position sizing. Logs all buy/sell/exit events when printlog=True.
    """
    params = dict(
        sma_short=10,               # period for fast SMA
        sma_long=30,                # period for slow SMA
        stop_loss_pct=0.02,         # 2% stop loss
        take_profit_pct=0.05,       # 5% take profit
        risk_per_trade_pct=0.01,    # risk 1% of account per trade
        printlog=False
    )

    def __init__(self):
        # Price series
        self.dataclose = self.datas[0].close

        # Indicators
        self.fast = bt.indicators.SMA(self.dataclose, period=self.p.sma_short)
        self.slow = bt.indicators.SMA(self.dataclose, period=self.p.sma_long)
        self.cross = bt.indicators.CrossOver(self.fast, self.slow)

        # Order handles
        self.order = None
        self.entry_price = None
        self.stop_order = None
        self.take_order = None

    def log(self, txt, dt=None):
        """
        Logging helper. Prints a line to stdout if printlog==True.
        """
        if not self.p.printlog:
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in (order.Submitted, order.Accepted):
            # Nothing to do on submit/accepted
            return

        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"BUY EXECUTED @ {order.executed.price:.2f}, size={order.executed.size}")
                self.entry_price = order.executed.price

                # Immediately place stop-loss and take-profit
                sl_price = self.entry_price * (1 - self.p.stop_loss_pct)
                tp_price = self.entry_price * (1 + self.p.take_profit_pct)
                size = order.executed.size

                # Stop-loss
                self.stop_order = self.sell(
                    exectype=bt.Order.Stop,
                    price=sl_price,
                    size=size
                )
                self.log(f"STOP-LOSS ORDER placed @ {sl_price:.2f} (size={size})")

                # Take-profit
                self.take_order = self.sell(
                    exectype=bt.Order.Limit,
                    price=tp_price,
                    size=size
                )
                self.log(f"TAKE-PROFIT ORDER placed @ {tp_price:.2f} (size={size})")

            elif order.issell():
                self.log(f"SELL EXECUTED @ {order.executed.price:.2f}, size={order.executed.size}")

                # If this sell was triggered by stop or take-profit, cancel the other
                if self.stop_order and self.stop_order.status not in (self.stop_order.Completed, self.stop_order.Cancelled):
                    self.cancel(self.stop_order)
                    self.log("Cancelled STOP-LOSS Order")
                if self.take_order and self.take_order.status not in (self.take_order.Completed, self.take_order.Cancelled):
                    self.cancel(self.take_order)
                    self.log("Cancelled TAKE-PROFIT Order")

                self.entry_price = None

        elif order.status in (order.Canceled, order.Margin, order.Rejected):
            self.log("Order Canceled/Margin/Rejected")

        # Reset current order handle
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(
            f"TRADE CLOSED | Gross PnL: {trade.pnl:.2f}, Net PnL: {trade.pnlcomm:.2f}"
        )

    def next(self):
        # Wait until both SMAs have enough bars
        min_bars = max(self.p.sma_short, self.p.sma_long)
        if len(self.data) < min_bars:
            return

        # If there is any pending order, do nothing
        if self.order:
            return

        # If not in position: check for buy signal
        if not self.position:
            if self.cross > 0:
                # Determine position size based on risk_per_trade_pct
                cash = self.broker.getcash()
                risk_amount = cash * self.p.risk_per_trade_pct
                potential_loss = self.dataclose[0] * self.p.stop_loss_pct
                size = int(risk_amount / potential_loss) if potential_loss > 0 else 0

                if size > 0:
                    self.log(f"BUY CREATE @ {self.dataclose[0]:.2f}, size={size}")
                    self.order = self.buy(size=size)
        else:
            # Already in position: check for sell signal
            if self.cross < 0:
                self.log(f"CLOSE CREATE @ {self.dataclose[0]:.2f}")
                self.order = self.close()

    def stop(self):
        self.log(f"FINAL PORTFOLIO VALUE: {self.broker.getvalue():.2f}")


class SmaWithTrailing(bt.Strategy):
    """
    SMA Crossover with a trailing stop.
    - Buy when fast SMA crosses above slow SMA.
    - Place a trailing stop immediately after entry.
    - Sell when either the stop is hit or SMA crosses below.
    """
    params = dict(
        fast=10,
        slow=30,
        trail_pct=0.03,     # 3% trailing stop
        printlog=False
    )

    def __init__(self):
        self.price = self.datas[0].close
        self.fast_sma = bt.indicators.SMA(self.price, period=self.p.fast)
        self.slow_sma = bt.indicators.SMA(self.price, period=self.p.slow)
        self.cross = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

        self.order = None
        self.trail_order = None

    def log(self, txt, dt=None):
        if not self.p.printlog:
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def next(self):
        min_bars = max(self.p.fast, self.p.slow)
        if len(self.data) < min_bars:
            return

        if self.order or self.trail_order:
            return

        if not self.position:
            if self.cross > 0:
                self.log(f"BUY CREATE @ {self.data.close[0]:.2f}")
                self.order = self.buy()
        else:
            if self.cross < 0:
                self.log(f"CLOSE CREATE @ {self.data.close[0]:.2f}")
                self.order = self.close()

    def notify_order(self, order):
        if order.status != order.Completed:
            # only act upon fully executed orders
            return

        if order.isbuy():
            entry_price = order.executed.price
            self.log(f"BUY EXECUTED @ {entry_price:.2f}")
            # Immediately place trailing stop
            self.trail_order = self.sell(
                exectype=bt.Order.StopTrail,
                trailpercent=self.p.trail_pct,
                size=order.executed.size
            )
            self.log(f"TRAILING STOP placed @ {self.p.trail_pct*100:.1f}%")

        elif order.issell():
            self.log(f"SELL EXECUTED @ {order.executed.price:.2f}")
            # Cancel any existing trailing stop (if still pending)
            if self.trail_order and self.trail_order.status not in (self.trail_order.Completed, self.trail_order.Cancelled):
                self.cancel(self.trail_order)
                self.log("Cancelled TRAILING STOP Order")
            self.trail_order = None

        self.order = None


class AtrPositionSizing(bt.Strategy):
    """
    Use Average True Range (ATR) to size positions by volatility:
    - Buy when fast SMA crosses above slow SMA.
    - Set a fixed stop at ATR * atr_mult below entry; risk is risk_perc of account.
    """
    params = dict(
        fast=10,
        slow=30,
        risk_perc=0.01,      # risk 1% of account per trade
        atr_period=14,
        atr_mult=3,          # stop distance = ATR × multiplier
        printlog=False
    )

    def __init__(self):
        self.price = self.datas[0].close
        self.fast = bt.indicators.SMA(self.price, period=self.p.fast)
        self.slow = bt.indicators.SMA(self.price, period=self.p.slow)
        self.cross = bt.indicators.CrossOver(self.fast, self.slow)

        self.atr = bt.indicators.ATR(self.datas[0], period=self.p.atr_period)
        self.order = None

    def log(self, txt, dt=None):
        if not self.p.printlog:
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def next(self):
        min_bars = max(self.p.fast, self.p.slow)
        if len(self.data) < min_bars:
            return

        if self.order:
            return

        cash = self.broker.getcash()
        if not self.position and self.cross > 0:
            # Determine stop distance using ATR
            stop_dist = self.atr[0] * self.p.atr_mult
            risk_amount = cash * self.p.risk_perc
            size = int(risk_amount / stop_dist) if stop_dist > 0 else 0

            if size > 0:
                self.log(f"BUY CREATE @ {self.data.close[0]:.2f}, size={size}")
                self.order = self.buy(size=size)
                # Place stop-loss immediately
                sl_price = self.data.close[0] - stop_dist
                stop_order = self.sell(
                    exectype=bt.Order.Stop,
                    price=sl_price,
                    size=size
                )
                self.log(f"STOP-LOSS ORDER placed @ {sl_price:.2f} (size={size})")
        elif self.position and self.cross < 0:
            self.log(f"CLOSE CREATE @ {self.data.close[0]:.2f}")
            self.order = self.close()

    def notify_order(self, order):
        if order.status in (order.Completed, order.Canceled, order.Rejected):
            # Always reset order handle after it’s done
            self.log(f"ORDER STATUS: {order.getstatusname()}")
            self.order = None


class TimedExitSma(bt.Strategy):
    """
    SMA crossover with a maximum holding period:
    - Buy when fast SMA crosses above slow SMA.
    - Sell either when SMA crosses below OR when max_hold bars have elapsed.
    """
    params = dict(
        fast=10,
        slow=30,
        max_hold=20,   # maximum bars per trade
        printlog=False
    )

    def __init__(self):
        self.price = self.datas[0].close
        self.fast = bt.indicators.SMA(self.price, period=self.p.fast)
        self.slow = bt.indicators.SMA(self.price, period=self.p.slow)
        self.cross = bt.indicators.CrossOver(self.fast, self.slow)

        self.entry_bar = None
        self.order = None

    def log(self, txt, dt=None):
        if not self.p.printlog:
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def next(self):
        min_bars = max(self.p.fast, self.p.slow)
        if len(self.data) < min_bars:
            return

        if self.order:
            return

        if not self.position and self.cross > 0:
            self.entry_bar = len(self)
            self.log(f"BUY CREATE @ {self.data.close[0]:.2f}")
            self.order = self.buy()
        elif self.position:
            # If slow SMA flips or max_hold is reached, close
            bars_held = len(self) - self.entry_bar
            if self.cross < 0:
                self.log(f"SELL CREATE (SMA flip) @ {self.data.close[0]:.2f}")
                self.order = self.close()
            elif bars_held >= self.p.max_hold:
                self.log(f"SELL CREATE (Max hold reached: {bars_held} bars) @ {self.data.close[0]:.2f}")
                self.order = self.close()

    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"BUY EXECUTED @ {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED @ {order.executed.price:.2f}")
        elif order.status in (order.Canceled, order.Margin, order.Rejected):
            self.log("Order Canceled/Margin/Rejected")

        self.order = None


class MultiTimeframeSma(bt.Strategy):
    """
    Multi-Timeframe SMA:
    - Primary feed (datas[0]) is intraday or daily.
    - Resampled weekly feed (datas[1]) for trend filter.
    - Buy only if fast SMA crosses above slow SMA on primary feed AND weekly close > weekly SMA.
    - Sell only if fast SMA crosses below slow SMA on primary feed AND weekly close < weekly SMA.
    """
    params = dict(
        fast=10,
        slow=30,
        printlog=False
    )

    def __init__(self):
        if len(self.datas) < 2:
            raise ValueError("MultiTimeframeSma requires two data feeds: daily and weekly")
        # Primary feed (intraday/day) at datas[0]
        price = self.datas[0].close
        self.fast = bt.indicators.SMA(price, period=self.p.fast)
        self.slow = bt.indicators.SMA(price, period=self.p.slow)
        self.cross = bt.indicators.CrossOver(self.fast, self.slow)

        # Weekly/resampled feed at datas[1]
        price_w = self.datas[1].close
        self.sma_w = bt.indicators.SMA(price_w, period=self.p.slow)

        self.order = None

    def log(self, txt, dt=None):
        if not self.p.printlog:
            return
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def next(self):
        # Ensure enough bars in both feeds
        if len(self.datas[0]) < self.p.fast or len(self.datas[1]) < self.p.slow:
            return

        trend_up = self.datas[1].close[0] > self.sma_w[0]
        trend_dn = self.datas[1].close[0] < self.sma_w[0]

        if self.order:
            return

        if not self.position and self.cross > 0 and trend_up:
            self.log(f"BUY CREATE @ {self.datas[0].close[0]:.2f} (Weekly trend UP)")
            self.order = self.buy()
        elif self.position and self.cross < 0 and trend_dn:
            self.log(f"SELL CREATE @ {self.datas[0].close[0]:.2f} (Weekly trend DOWN)")
            self.order = self.sell()

    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"BUY EXECUTED @ {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED @ {order.executed.price:.2f}")
        elif order.status in (order.Canceled, order.Margin, order.Rejected):
            self.log("Order Canceled/Margin/Rejected")

        self.order = None
