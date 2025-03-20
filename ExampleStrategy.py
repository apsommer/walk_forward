import pandas as pd
from backtesting import Strategy

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