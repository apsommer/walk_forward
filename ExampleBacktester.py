from backtesting import Backtest
import DataLayer as dl
from ExampleStrategy import BuyLowSellHighStrategy
import matplotlib.pyplot as plt

# constants
starting_date = "2024-10-15"
ending_date = "2025-01-01"
schema = "ohlcv-1m"

df_prices = dl.getPrices(
    starting_date,
    ending_date,
    schema)

bt = Backtest(df_prices, BuyLowSellHighStrategy, cash=10_000_000, commission=0, exclusive_orders=True)
stats = bt.run()
print(stats)

filename = "df_prices.xlsx"
df_prices.to_excel(filename)

# bt.plot(results=stats)
plt.plot(df_prices)
plt.show()