from backtesting import Backtest
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import datetime
import math
import DataLayer
from ExampleStrategy import BuyLowSellHighStrategy

df_prices = DataLayer.getPrices()
initial_cash = DataLayer.initial_cash

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