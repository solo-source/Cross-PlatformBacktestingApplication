# Cross-Platform Backtesting App

A modular, open-source GUI application for backtesting trading strategies, built with:

- **Backtrader** as the core backtesting engine  
- **PySide6 (Qt for Python)** for a responsive, cross-platform desktop GUI  
- **Historical data** support (CSV files & Yahoo Finance via `yfinance`)  
- **Live data** support out of the box  
  - **REST polling** (any JSON-returning endpoint)  
  - **WebSocket streaming** (e.g. Binance, Coinbase, or custom feeds)  
- **Built-in strategies** (e.g. SMA crossover with stop-loss and take-profit)  
- **Custom strategy configuration** via GUI dialog  
- **Embedded Matplotlib charts** for equity curves, price series, and indicators  
- **Comprehensive logging** and error handling  

---  

## Features

- **Historical Backtesting**  
  - Load OHLCV CSV files (`Date,Open,High,Low,Close,Volume`)  
  - Fetch data from Yahoo Finance (`yfinance`)  
- **Live Data Streaming**  
  - REST endpoint polling with configurable interval  
  - WebSocket subscription for real-time price updates  
- **Strategy Configuration**  
  - SMA crossover with risk controls (stop-loss, take-profit, position sizing)  
  - Extendable to custom strategies via GUI  
- **Visualization**  
  - Equity curve, price chart, and performance metrics displayed in-app  
- **Logging & Diagnostics**  
  - All errors and key events logged to `app.log`  
  - User notifications via dialog boxes  

---  

## Installation (Fedora Linux)

1. **Install system dependencies**  
   ```bash
   sudo dnf install python3 python3-venv python3-pip
   git clone https://github.com/solo-source/backtester_app.git
   cd backtester_app

Create and activate a virtual environment

    python3 -m venv venv
    source venv/bin/activate

Install Python dependencies

    pip install -r requirements.txt

Quick Start

    Run the application

    python -m src.gui.main_window

Load historical data

        Click Load CSV and select a CSV file with headers Date,Open,High,Low,Close,Volume.

        (Optional) Click Load Yahoo (future enhancement) to fetch from Yahoo Finance.

Start live data stream

        REST: Prepare a text file containing your REST API URL, click Start REST Stream, and select that file.

        WebSocket: Click Start WS Stream (defaults to Binance’s BTC/USDT trades).

Configure and run strategy

        Enter SMA Short and SMA Long periods on the left panel.

        Click Run Backtest.

View results

        Chart updates in the right panel (price series or equity curve).

        Check performance metrics printed in console or displayed within the GUI.

        Review app.log for detailed logs and any error messages.

Testing

Run unit and integration tests with pytest:

    pytest

Tests cover data loading, strategy execution, and engine integration.
Extending & Contributing

    Add new strategies: Edit or add classes in src/backtester/strategies.py.

    New data sources: Extend src/data/loader.py (historical) or src/data/stream.py (live).

    Improve UI: Modify or add dialogs in src/gui/.

    Submit issues or PRs on GitHub—this project is open-source and community-driven!

License

This project is licensed under the MIT License. See LICENSE for details.

