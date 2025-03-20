import databento as db
import local.api_keys as keys

# constants
initial_cash = 10_000_000_000_000

# request network data synchronous!
client = db.Historical(keys.bento_api_key)
starting_date = "2024-06-15" # "2022-01-03"
ending_date = "2025-01-01"

df_prices = (client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["NQ.v.0"],
        stype_in="continuous",
        schema="ohlcv-1m",
        start=starting_date,
        end=ending_date)
             .to_df())

# format names
df_prices.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)

def getPrices():
    return df_prices