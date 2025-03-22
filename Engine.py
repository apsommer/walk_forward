from backtesting import Backtest
import DataLayer as dl
from ExampleStrategy import BuyLowSellHighStrategy
import matplotlib.pyplot as plt

from LiveStrategy import LiveStrategy

# constants
starting_date = "2024-01-01"
ending_date = "2025-01-01"
schema = "ohlcv-1m"

df_prices = dl.getPrices(
    starting_date,
    ending_date,
    schema)

bt = Backtest(
    df_prices,
    LiveStrategy,
    cash=10_000_000,
    commission=0,
    exclusive_orders=True)
stats = bt.run()

# write
# df_prices.to_excel("df_prices.xlsx")
df_prices.to_csv("df_prices.csv")
stats.to_csv("stats.csv")
print(stats)

# plot
plt.plot(df_prices)
plt.show()