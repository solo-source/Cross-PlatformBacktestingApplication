```markdown
# User Manual

## Loading Data
- **Historical CSV**: Click **Load CSV**, select file with headers `Date,Open,High,Low,Close,Volume`.
- **REST Stream**: Prepare a text file containing your REST API URL, click **Start REST Stream**, select the file.
- **WebSocket**: Click **Start WS Stream** (defaults to Binance BTC/USDT trade).

## Configuring Strategy
1. Enter **SMA Short** and **SMA Long** periods.
2. Click **Run Backtest**.

## Viewing Results
- Price series or equity curve displays in the right panel.
- Check `app.log` for detailed logs and errors.

## Extending
- To add new strategies, edit `src/backtester/strategies.py`.
- To support new data sources, update `src/data/loader.py` or `stream.py`.

