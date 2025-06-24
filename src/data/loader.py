# src/data/loader.py
"""
DataLoader: load historical data from CSV or Yahoo Finance.
"""

import backtrader as bt
import pandas as pd
import yfinance as yf
from typing import Tuple

class DataLoader:
    """Load historical data as Backtrader data feeds."""

    @staticmethod
    def from_csv(filepath: str) -> Tuple[bt.feeds.PandasData, int]:
        """
        Load OHLCV data from a CSV file with header:
        Date,Open,High,Low,Close,Volume

        Returns:
          feed      - Backtrader PandasData feed
          row_count - number of rows read from CSV
        """
        # 1) Read CSV into DataFrame
        df = pd.read_csv(
            filepath,
            parse_dates=['Date'],
            dtype={
                'Open': float,
                'High': float,
                'Low': float,
                'Close': float,
                'Volume': int
            }
        )
        row_count = df.shape[0]
        # print(f"[DataLoader] CSV read: {row_count} rows, columns={list(df.columns)}")
        # if row_count == 0:
        #     raise ValueError("DataLoader.from_csv: CSV file is empty")

        # 2) Prepare 'datetime' column for Backtrader
        df.rename(columns={'Date': 'datetime'}, inplace=True)
        df.sort_values('datetime', inplace=True)

        # 3) Add openinterest column (required by PandasData)
        df['openinterest'] = 0

        # 4) Debug: show first few rows
        # print(df.head(3))

        # 5) Create the PandasData feed with explicit column mapping
        feed = bt.feeds.PandasData(
            dataname=df,
            datetime='datetime',   # column name in df
            open='Open',
            high='High',
            low='Low',
            close='Close',
            volume='Volume',
            openinterest='openinterest'
        )

        return feed, row_count

    @staticmethod
    def from_yfinance(symbol: str, start: str, end: str) -> bt.feeds.PandasData:
        """
        Fetch historical data via yfinance and convert to PandasData feed.
        """
        # Download and prepare DataFrame
        df = yf.download(symbol, start=start, end=end)
        df.reset_index(inplace=True)
        df.rename(columns={'Date': 'datetime'}, inplace=True)
        df['openinterest'] = 0

        # Create the PandasData feed
        feed = bt.feeds.PandasData(
            dataname=df,
            datetime='datetime',
            open='Open',
            high='High',
            low='Low',
            close='Close',
            volume='Volume',
            openinterest='openinterest'
        )
        return feed
