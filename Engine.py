import pandas as pd
from backtesting import Backtest
import DataLayer as data
from LiveStrategy import LiveStrategy

# constants
csv_filename = "data/nq_last_6mon_2024-09-15_2025-03-15.csv"
symbol = "NQ.v.0"
schema = "ohlcv-1m"
starting_date = "2024-09-15"
ending_date = "2025-03-15"

# todo download prices costs $
df_prices = data.getPrices(
    csv_filename=csv_filename, # todo read from csv instead
    symbol=symbol,
    schema=schema,
    starting_date=starting_date,
    ending_date=ending_date)
# df_prices.to_excel(csv_filename.replace(".csv", ".xlsx"))
# df_prices.to_csv(csv_filename)

bt = Backtest(
    df_prices,
    LiveStrategy,
    cash=10_000_000,
    commission=0,
    exclusive_orders=True)
stats = bt.run()

# stats.to_csv("stats.csv")
# plt.plot(df_prices)
# plt.show()
print(stats)
bt.plot()
