import pandas as pd
from backtesting import Strategy, Backtest
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import datetime
import math
import databento as db

# todo need to constantly create new api key on free tier
#  https://databento.com/portal/keys
client = db.Historical("db-L7H6PYyUMffBwBqn4fTBPJ5JkTyqn")
starting_date = "2022-01-03"
ending_date = "2025-01-01"

df_prices = (client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["NQ.v.0"],
        stype_in="continuous",
        schema="ohlcv-1m",
        start=starting_date,
        end=ending_date)
             .to_df())

# normalize timestamps
df_prices.index = df_prices.index.tz_localize(None)

# format names
df_prices.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
# print(df_prices.to_markdown())

# Strategy ##########

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

initial_cash = 10_000_000_000_000

# run strategy and output results
bt = Backtest(df_prices, BuyLowSellHighStrategy, cash=initial_cash, commission=0, exclusive_orders=True)
stats = bt.run()
print(stats)

# optimize / sweep params for lookback periods
stats, heatmap = bt.optimize(
    n_high=range(20, 60, 5), # optimization steps range(low, high, step)
    n_low=range(20, 60, 5), # optimization steps range(low, high, step)
    # constraint=lambda p: p.n_high > p.n_low, # optional additional constraints
    maximize='Equity Final [$]', # fitness function as predefined column name from backtesting.py, consider 'Sharpe Ratio'
    method = 'grid',
    # max_tries=56,
    random_state=0,
    return_heatmap=True)

sns.heatmap(heatmap.unstack())
plt.show()

########## WALK FORWARD TEST ##########

iterations = [
    {
        'in_sample': [datetime(2022,1,1),datetime(2023,1,1)],
        'out_of_sample': [datetime(2023,1,1),datetime(2023,5,1)]
    },
    {
        'in_sample': [datetime(2022,5,1),datetime(2023,5,1)],
        'out_of_sample': [datetime(2023,5,1),datetime(2023,9,1)]
    },
    {
        'in_sample': [datetime(2022,9,1),datetime(2023,9,1)],
        'out_of_sample': [datetime(2023,9,1),datetime(2024,1,1)]
    },
    {
        'in_sample': [datetime(2023,1,1),datetime(2024,1,1)],
        'out_of_sample': [datetime(2024,1,1),datetime(2024,5,1)]
    },
    {
        'in_sample': [datetime(2023,5,1),datetime(2024,5,1)],
        'out_of_sample': [datetime(2024,5,1),datetime(2024,9,1)]
    },
    {
        'in_sample': [datetime(2023, 9, 1), datetime(2024, 9, 1)],
        'out_of_sample': [datetime(2024, 9, 1), datetime(2025, 1, 1)]
    }
]

report = []

for iter in tqdm(iterations):

    # isolate price data IS and OOS portions
    df_is = df_prices[(df_prices.index >= iter['in_sample'][0]) & (df_prices.index <= iter['in_sample'][1])]
    df_oos = df_prices[(df_prices.index >= iter['out_of_sample'][0]) & (df_prices.index <= iter['out_of_sample'][1])]

    # create default backtest
    bt_is = Backtest(df_is, BuyLowSellHighStrategy, cash=initial_cash, commission=0, exclusive_orders=True)

    # optimize / sweep walk forward params
    stats_is, heatmap = bt_is.optimize(
        n_high=range(20, 60, 5),
        n_low=range(20, 60, 5),
        maximize='Sharpe Ratio', # bt.run output column names
        method='grid',
        max_tries=64,
        random_state=0,
        return_heatmap=True)

    # extract the optimal params
    BuyLowSellHighStrategy.n_high = stats_is._strategy.n_high
    BuyLowSellHighStrategy.n_low = stats_is._strategy.n_low

    # run optimized params on OS portion
    bt_oos = Backtest(df_oos, BuyLowSellHighStrategy, cash=initial_cash, commission=0, exclusive_orders=True)
    stats_oos = bt_oos.run()
    print(stats_oos)

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
        'n_low': stats_oos._strategy.n_low,
        'exposure': stats_oos['Exposure Time [%]'],
        'bh_scaled': stats_oos['Buy & Hold Return [%]'] * stats_oos['Exposure Time [%]'] / 100,
        'is_heatmap': heatmap,
        'sharpe_is': stats_is['Sharpe Ratio'],
    })

# plot IS heatmaps
plt.rcParams['figure.figsize'] = [20, 10]
rows = len(report)
for idx, res in enumerate(report):
    plt.subplot(math.floor(rows/2), math.ceil(rows/2), idx+1)
    plt.title(f"Iter # {idx+1} - Year {res['start_date'].year}")
    sns.heatmap(res['is_heatmap'].unstack())
plt.show()