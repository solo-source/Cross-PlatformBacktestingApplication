# Application User Manual

Welcome to the **Modular Backtester** application — a GUI-driven backtesting tool for financial strategies. This guide walks you through each feature and component, so you can effectively load data, configure strategies, run backtests, and manage results.

---

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Launching the App](#launching-the-app)
3. [Data Tab](#data-tab)
   - [Historical CSV Loader](#historical-csv-loader)
   - [Live / WebSocket Loader](#live--websocket-loader)
4. [Strategy Configuration](#strategy-configuration)
5. [Running a Backtest](#running-a-backtest)
6. [Results Tab](#results-tab)
   - [Equity Curve](#equity-curve)
   - [Drawdown Plot](#drawdown-plot)
   - [Returns Distribution](#returns-distribution)
7. [Snapshots (Upload / History)](#snapshots-upload--history)
   - [Saving a Snapshot](#saving-a-snapshot)
   - [Refreshing History](#refreshing-history)
   - [Previewing Saved Charts](#previewing-saved-charts)
8. [Logging & Troubleshooting](#logging--troubleshooting)
9. [Extending the Application](#extending-the-application)

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/solo-source/Cross-PlatformBacktestingApplication.git
   cd Cross-PlatformBacktestingApplication
   ```
2. **Create a virtual environment & install dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
3. **(Optional) Install dev dependencies** for testing:
   ```bash
   pip install -r requirements-dev.txt
   ```

---

## Launching the App

Run:
```bash
python -m src.gui.main_window
```
The main window will open maximized on your screen.

---

## Data Tab

The **Data** tab has two loaders. Use the **Data Source** toggle on the left to switch between them.

### Historical CSV Loader
- Click **Browse CSV**.
- Select a CSV file with columns: `Date, Open, High, Low, Close, Volume`.
- The last 100 rows display in the table below.
- The app also initializes its internal backtesting feed from this data.

### Live / WebSocket Loader
- Enter a ticker (e.g. `SPY`) and polling interval in minutes.
- Click **Start Live Feed** to begin yfinance polling.
- The table updates with the most recent 100 bars.
- Or click **Browse CSV** here to fall back to a local file.

---

## Strategy Configuration

On the left panel:
- **Data Source**: Choose CSV or WS.
- **Strategy Selector**: Pick one of:
  - SMA Crossover
  - SMA with Trailing Stop
  - ATR-based Position Sizing
  - Timed Exit SMA
  - Multi-Timeframe SMA
- Adjust parameters (periods, stop-loss %, etc.) via spin boxes.

---

## Running a Backtest

Click **Run Backtest** in the left panel:
1. The selected data feed(s) attach to Backtrader’s engine.
2. The chosen strategy class runs with your parameters.
3. Analyses (TimeReturn, DrawDown) compute behind the scenes.
4. Plots appear in the **Results** tab.

---

## Results Tab

The Results tab is scrollable and contains three plots, each with axis labels and interactive toolbar controls.

### Equity Curve
- X-axis: **Date**
- Y-axis: **Portfolio Value**
- Shows cumulative portfolio evolution over time.

### Drawdown Plot
- X-axis: **Time**
- Y-axis: **Drawdown (%)**
- Highlights periods of peak-to-trough drawdown.

### Returns Distribution
- X-axis: **Returns** (period-over-period gains)
- Y-axis: **Frequency**
- Displays a histogram of returns.

Use the toolbar to pan, zoom, or save the plot images.

---

## Snapshots (Upload / History)

Switch to the **Upload/History** tab to save and review backtest runs.

### Saving a Snapshot
1. After running a backtest, fill in:
   - **Symbol**, **Title**, **Description**, **Notes**
   - **Live** checkbox if data was streaming.
   - **Date** (defaults to today).
2. Click **Save Snapshot**.
3. The three chart PNGs (Equity, Drawdown, Histogram) are stored in a local SQLite database.

### Refreshing History
- Click **Refresh History** to reload the table of saved runs.
- Columns: **ID**, **Symbol**, **Date**, **Title**, **Live**.

### Previewing Saved Charts
- Click on a row to open the **Snapshot Preview** dialog.
- High-resolution (1920×1080) images appear side-by-side in a scrollable viewer.

---

## Logging & Troubleshooting

- All debug and error messages write to `app.log` in the project root.
- If data loading or backtest errors occur, pop-up dialogs describe the issue.
- Common fixes:
  - Ensure CSV headers match exactly.
  - Check you have enough data bars for the chosen SMA periods.

---

## Extending the Application

- **Add a new strategy**: implement a subclass in `src/backtester/strategies.py` and add it to `StrategySelectorWidget.STRATEGIES`.
- **New data source**: extend `src/data/loader.py` or create a new streamer in `src/gui/ws_window.py` or similar.
- **Custom charts**: modify `_setup_plots` in `main_window.py` or add new tabs.

For contributions:
1. Fork the repo and create a feature branch.
2. Add tests under `tests/` and update `requirements-dev.txt` if needed.
3. Submit a PR with descriptive commits and ensure CI passes.

---

Thank you for using **Modular Backtester**! Feel free to raise issues or contribute enhancements on GitHub.