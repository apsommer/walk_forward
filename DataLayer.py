import logging
import sys
import databento as db
import pandas as pd
import local.api_keys as keys

log_format = "%(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=log_format)

def logm(message):
        logging.info(message)

def getOhlc(
    csv_filename = None,
    symbol = "NQ.v.0",
    schema = "ohlcv-1m",
    starting_date = "2024-10-01",
    ending_date = "2025-01-01"):

    # return cached data in csv format
    if csv_filename is not None:

        logm("Upload ohlc from " + csv_filename)

        ohlc = pd.read_csv(csv_filename, index_col=0)
        ohlc.index = pd.to_datetime(ohlc.index)
        return ohlc

    logm("Download ohlc from databento ...")

    # request network data synchronous!
    client = db.Historical(keys.bento_api_key)
    ohlc = (client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=[symbol],
        stype_in="continuous",
        schema=schema,
        start=starting_date,
        end=ending_date).to_df())

    # rename, drop
    ohlc.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
    ohlc.index.rename("timestamp", inplace=True)
    ohlc = ohlc[ohlc.columns.drop(['symbol', 'rtype', 'instrument_id', 'publisher_id', 'volume'])]

    # normalize timestamps
    ohlc.index = ohlc.index.tz_localize(None)
    ohlc.index = pd.to_datetime(ohlc.index)

    return ohlc