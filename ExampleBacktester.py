from backtesting import Backtest
import DataLayer as dl
from ExampleStrategy import BuyLowSellHighStrategy

df_prices = dl.getPrices()
initial_cash = dl.initial_cash

bt = Backtest(df_prices, BuyLowSellHighStrategy, cash=initial_cash, commission=0, exclusive_orders=True)
stats = bt.run()
print(stats)
