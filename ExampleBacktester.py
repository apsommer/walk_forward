from backtesting import Backtest
import DataLayer as dl
from ExampleStrategy import BuyLowSellHighStrategy
import pandas as pd

# constants
initial_cash = 10_000_000_000_000
starting_date = "2024-10-15"
ending_date = "2025-01-01"
filename = "df_prices.xlsx"

df_prices = dl.getPrices(
    starting_date,
    ending_date)

bt = Backtest(df_prices, BuyLowSellHighStrategy, cash=initial_cash, commission=0, exclusive_orders=True)
stats = bt.run()
print(stats)

df_prices.to_excel(filename)

# bt.plot() # todo backtesting.py does not appear able to plot 1m candles?