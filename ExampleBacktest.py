from backtesting import Backtest
import seaborn as sns
import matplotlib.pyplot as plt

import DataLayer
from ExampleEngine import initial_cash
from ExampleStrategy import BuyLowSellHighStrategy

df_prices = DataLayer.getPrices()
initial_cash = initial_cash

# run strategy and output results
bt = Backtest(df_prices, BuyLowSellHighStrategy, cash=initial_cash, commission=0, exclusive_orders=True)
stats = bt.run()
print(stats)

# optimize / sweep params for lookback periods
stats, heatmap = bt.optimize(
    n_high=range(20, 60, 10), # optimization steps range(low, high, step)
    n_low=range(20, 60, 10), # optimization steps range(low, high, step)
    # constraint=lambda p: p.n_high > p.n_low, # optional additional constraints
    maximize='Equity Final [$]', # fitness function as predefined column name from backtesting.py, consider 'Sharpe Ratio'
    method = 'grid',
    # max_tries=56,
    random_state=0,
    return_heatmap=True)

sns.heatmap(heatmap.unstack())
plt.show()

