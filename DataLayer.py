import databento as db
import local.api_keys as keys

# request network data synchronous!
client = db.Historical(keys.bento_api_key)

def getPrices(
    starting_date,
    ending_date):

    df_prices = (client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["NQ.v.0"],
        stype_in="continuous",
        schema="ohlcv-1m",
        start=starting_date,
        end=ending_date)
                 .to_df())

    # format names, normalize timestamps
    df_prices.index = df_prices.index.tz_localize(None)
    df_prices.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"},
                     inplace=True)
    df_prices.index.rename("timestamp", inplace=True)

    # remove unwanted columns
    clean = df_prices[df_prices.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id'])]
    return clean