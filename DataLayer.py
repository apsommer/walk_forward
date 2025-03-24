import databento as db
import pandas as pd

import local.api_keys as keys

# request network data synchronous!
client = db.Historical(keys.bento_api_key)

def getPrices(
    starting_date = "2024-10-01",
    ending_date = "2025-01-01",
    schema = "ohlcv-1m"):

    df_prices = (client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["NQ.v.0"],
        stype_in="continuous",
        schema=schema,
        start=starting_date,
        end=ending_date)
                 .to_df())

    # rename, drop
    df_prices.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
    df_prices.index.rename("timestamp", inplace=True)
    df_prices = df_prices[df_prices.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]

    # normalize timestamps
    df_prices.index = df_prices.index.tz_localize(None)
    df_prices.index = pd.to_datetime(df_prices.index) #, format="%m/%d/%Y %I:%M:%S %p")

    return df_prices