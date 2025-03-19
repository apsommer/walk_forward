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