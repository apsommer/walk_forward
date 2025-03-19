import yfinance

import yfinance as yf
import pandas as pd
from backtesting import Strategy, Backtest
import seaborn as sns
from tqdm import tqdm

TICKER = 'AAPL'
START_DATE = '2015-01-01'
END_DATE = '2022-12-31'
FREQUENCY = '1d'

# get AAPL daily stock price between 2015-22 from yfinance
df_prices = yf_ticker = yf.Ticker(TICKER).history(start=START_DATE,end=END_DATE,interval=FREQUENCY)

# normalize timestamps
df_prices.index = df_prices.index.tz_localize(None)

# watermarks of SMA over lookback periods
def high_watermark(highs, lookback):
    return pd.Series(highs).rolling(lookback).max()
def low_watermark(lows, lookback):
    return pd.Series(lows).rolling(lookback).min()

