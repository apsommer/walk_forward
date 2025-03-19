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

class BuyLowSellHighStrategy(Strategy):
    n_high = 30
    n_low = 30

    def init(self):

        # define indicators
        self.high_watermark = self.I(high_watermark, self.data.Close, self.n_high)
        self.low_watermark = self.I(low_watermark, self.data.Close, self.n_low)

    def next(self):

        # strat is long only
        # if position is flat
        if not self.position:

            # and this is the low watermark, then buy
            if self.low_watermark[-1] == self.data.Close[-1]:
                self.buy()

        # if position is long and this is the high watermark
        elif self.high_watermark[-1] == self.data.Close[-1]:
            self.position.close()