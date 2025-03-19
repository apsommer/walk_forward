import yfinance as yf
import pandas as pd
from backtesting import Strategy, Backtest
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import datetime

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

########## TEST ##########

# run strategy and output results
bt = Backtest(df_prices, BuyLowSellHighStrategy, cash=10_000, commission=0, exclusive_orders=True)
stats = bt.run()
print(stats)

# optimize / sweep params for lookback periods
stats, heatmap = bt.optimize(
    n_high=range(20, 60, 5), # optimization steps range(low, high, step)
    n_low=range(20, 60, 5), # optimization steps range(low, high, step)
    # constraint=lambda p: p.n_high > p.n_low, # optional additional constraints
    maximize='Equity Final [$]', # fitness function as predefined column name from backtesting.py, consider 'Sharpe Ratio'
    method = 'grid',
    max_tries=56,
    random_state=0,
    return_heatmap=True)

sns.heatmap(heatmap.unstack())
plt.show()

########## WALK FORWARD TEST ##########

# 3 years IS, 1 year OOS
# unanchored, sliding four year window
iterations = [
    {
        'in_sample': [datetime(2015,1,1),datetime(2017,12,31)],
        'out_of_sample': [datetime(2018,1,1),datetime(2018,12,31)]
    },
    {
        'in_sample': [datetime(2016,1,1),datetime(2018,12,31)],
        'out_of_sample': [datetime(2019,1,1),datetime(2019,12,31)]
    },
    {
        'in_sample': [datetime(2017,1,1),datetime(2019,12,31)],
        'out_of_sample': [datetime(2020,1,1),datetime(2020,12,31)]
    },
    {
        'in_sample': [datetime(2018,1,1),datetime(2020,12,31)],
        'out_of_sample': [datetime(2021,1,1),datetime(2021,12,31)]
    },
    {
        'in_sample': [datetime(2019,1,1),datetime(2021,12,31)],
        'out_of_sample': [datetime(2022,1,1),datetime(2022,12,31)]
    },
]

report = []

for iter in tqdm(iterations):

    # isolate price data IS and OOS portions
    df_is = df_prices[(df_prices.index >= iter['in_sample'][0]) & (df_prices.index <= iter['in_sample'][1])]
    df_oos = df_prices[(df_prices.index >= iter['out_of_sample'][0]) & (df_prices.index <= iter['out_of_sample'][1])]

    # backtest default strat
    bt_is = Backtest(df_is, BuyLowSellHighStrategy, cash=10_000, commission=0, exclusive_orders=True)

    # optimize / sweep walk forward params
    stats_is, heatmap = bt_is.optimize(
        n_high=range(20, 60, 5),
        n_low=range(20, 60, 5),
        maximize='Equity Final [$]',
        method='grid',
        max_tries=64,
        random_state=0,
        return_heatmap=True)

    # extract the optimal params
    BuyLowSellHighStrategy.n_high = stats_is._strategy.n_high
    BuyLowSellHighStrategy.n_low = stats_is._strategy.n_low

    # run optimized params on OS portion
    bt_oos = Backtest(df_oos, BuyLowSellHighStrategy, cash=10_000, commission=0, exclusive_orders=True)
    stats_oos = bt_oos.run()

    # construct text output summary
    report.append({
        'start_date': stats_oos['Start'],
        'end_date': stats_oos['End'],
        'return_strat': stats_oos['Return [%]'],
        'max_drawdown': stats_oos['Max. Drawdown [%]'],
        'ret_strat_ann': stats_oos['Return (Ann.) [%]'],
        'volatility_strat_ann': stats_oos['Volatility (Ann.) [%]'],
        'sharpe_ratio': stats_oos['Sharpe Ratio'],
        'return_bh': stats_oos['Buy & Hold Return [%]'],
        'n_high': stats_oos._strategy.n_high,
        'n_low': stats_oos._strategy.n_low
    })

print(pd.DataFrame(report))