from backtesting import Backtest
import Repository as data
from LiveStrategy import LiveStrategy
from tabulate import tabulate

# constants
csv_filename = "data/nq_6months_2024-09-15_2025-03-15.csv"
starting_date = "2024-09-15"
# csv_filename = "data/nq_2years_2023-03-15_2025-03-15.csv"
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
# df_prices.to_csv(csv_filename)
# df_prices.to_excel(csv_filename.replace(".csv", ".xlsx"))

# todo read from csv instead
ohlc = data.getOhlc(csv_filename=csv_filename)
bt = Backtest(
    ohlc,
    LiveStrategy,
    cash=10_000_000,
    commission=0,
    exclusive_orders=True)
stats = bt.run()

# plt.plot(df_prices)
# plt.show()
# bt.plot()

print(stats)
print(str(stats['_trades']))
print(
    tabulate(
        stats,
        headers='keys',
        tablefmt='psql'))

