import databento as db
import local.api_keys as keys

client = db.Historical(keys.bento_api_key)
starting_date = "2022-01-03"
ending_date = "2025-01-01"

df_prices = (client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["NQ.v.0"],
        stype_in="continuous",
        schema="ohlcv-1m",
        start=starting_date,
        end=ending_date)
             .to_df())

# normalize timestamps
df_prices.index = df_prices.index.tz_localize(None)

# format names
df_prices.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
# print(df_prices.to_markdown())

def getPrices():
    return df_prices