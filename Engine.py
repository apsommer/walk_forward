from backtesting import Backtest
import DataLayer as data
from LiveStrategy import LiveStrategy

# constants
csv_filename = "data/nq_last_6mon_2024-09-15_2025-03-15.csv"
starting_date = "2024-09-15"
# csv_filename = "data/nq_last_2years_2023-03-15_2025-03-15.csv"
# starting_date = "2023-03-15"
ending_date = "2025-03-15"
symbol = "NQ.v.0"
schema = "ohlcv-1m"

# todo download prices costs $
# df_prices = data.getPrices(
#     symbol=symbol,
#     schema=schema,
#     starting_date=starting_date,
#     ending_date=ending_date)
# df_prices.to_excel(csv_filename.replace(".csv", ".xlsx"))
# df_prices.to_csv(csv_filename)

# todo read from csv instead
df_prices = data.getOhlc(csv_filename=csv_filename)
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
# bt.plot()
