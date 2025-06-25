# Cross-Platform Backtesting Application

A modular, open-source desktop GUI application for backtesting trading strategies using historical or live market data.

---

## 🚀 Features

### ✅ Backtesting Engine
- Built on top of [Backtrader](https://www.backtrader.com/)
- Support for multiple data sources:
  - CSV-based historical OHLCV
  - Real-time feeds via WebSocket from Yahoo Finance (`yfinance`)

### ✅ GUI Interface (PySide6)
- Intuitive layout: Data source panel, strategy selector, results viewer
- Modular tabbed interface (Data, Results, Upload/History)
- Embedded interactive Matplotlib charts:
  - Equity Curve
  - Drawdown
  - Returns Distribution

### ✅ Strategy Configuration
- Strategy selector with parameter customization
- SMA crossover and multi-timeframe examples included
- Supports custom user-defined strategies

### ✅ Snapshot & History
- Save snapshot (charts + metadata) to SQLite DB
- View saved snapshots in scrollable preview
- Interactive image display for Equity, Drawdown, Histogram

### ✅ Logging & Testing
- Logs saved to `app.log`
- Unit tests with `pytest` and `pytest-qt` for GUI testing

---

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Linux (tested on Fedora), Windows, macOS

### Setup
```bash
# System dependencies (Fedora)
sudo dnf install python3 python3-venv python3-pip git

# Clone repository
git clone https://github.com/solo-source/backtester_app.git
cd backtester_app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## 🚦 Quick Start

```bash
python -m src.gui.main_window
```

### Load Data
- Click **Load CSV** and select a file with `Date,Open,High,Low,Close,Volume` columns.
- (Live data via WebSocket polling supported; REST feed also supported.)

### Run Strategy
- Choose a strategy (e.g., SmaCross).
- Enter parameters like `sma_short` and `sma_long`.
- Click **Run Backtest**.

### View Results
- Navigate to the **Results** tab to view:
  - Equity curve
  - Drawdown chart
  - Returns histogram
- All plots are interactive and zoomable.

---

## 💾 Snapshots & History

- Save snapshots via the **Upload/History** tab.
- View previous runs and load saved plots interactively.
- Data stored in `snapshots.db` SQLite file.

---

## 🧪 Running Tests

```bash
pytest
```

Tests are located in the `tests/` folder:
- CSV loading
- Backtest engine integration
- Strategy validation
- GUI component behavior (`pytest-qt`)

---

## 📁 Project Structure

```
src/
├── backtester/         # Core engine logic
├── data/               # Data loading modules (CSV, REST, WebSocket)
├── gui/                # PySide6 GUI modules
├── utils/              # Logging and utility helpers
├── viz/                # Chart canvas and Matplotlib setup
tests/                  # Test cases for engine, loader, GUI
snapshots.db            # SQLite database of saved snapshots
requirements.txt
README.md
```

---

## 🔧 Extending

- Add strategies in `src/backtester/strategies.py`
- Add new loaders in `src/data/`
- Modify GUI in `src/gui/`
- Submit pull requests and open issues on GitHub!

---

## 📄 License

This project is licensed under the MIT License.  
See `LICENSE` for details.