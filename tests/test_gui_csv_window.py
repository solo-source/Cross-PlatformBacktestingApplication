import pytest
import pandas as pd
from PySide6.QtWidgets import QApplication
from src.gui.csv_window import CsvBacktestWindow

@pytest.fixture(scope="module")
def app():
    return QApplication([])

def test_csv_widget_load_and_get_feed(tmp_path, app):
    # create a CSV
    df = pd.DataFrame({
        'Date': pd.date_range('2021-01-01', periods=10),
        'Open': range(10), 'High': range(10),
        'Low': range(10), 'Close': range(10), 'Volume': [100]*10
    })
    csv = tmp_path / "data.csv"
    df.to_csv(csv, index=False)

    w = CsvBacktestWindow()
    # simulate loading
    w.df = df
    w.data_rows = len(df)
    feed_list = w.get_datafeed()
    assert isinstance(feed_list, list) and len(feed_list) == 1
    f = feed_list[0]
    assert hasattr(f, 'lines')
    # check first close value
    assert f.lines.close[0] == df.Close.iloc[0]

def test_error_if_not_loaded(app):
    w = CsvBacktestWindow()
    with pytest.raises(RuntimeError):
        w.get_datafeed()
