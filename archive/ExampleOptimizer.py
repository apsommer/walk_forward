from backtesting import Backtest
import seaborn as sns
import matplotlib.pyplot as plt
from Repository import getOhlc
from ExampleStrategy import BuyLowSellHighStrategy

# constants
starting_date = "2023-12-15"
ending_date = "2025-01-01"

df_prices = getOhlc(starting_date, ending_date)

# run strategy and output results
bt = Backtest(df_prices, BuyLowSellHighStrategy, cash=10_000_000_000_000, commission=0, exclusive_orders=True)
stats = bt.run()
print(stats)

# optimize by sweep params for lookback periods n_high, n_low
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

