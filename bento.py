import databento as db

client = db.Historical("db-HKrvWfTtEGucr3M6T7EJd5nQmQUyH")

# data = client.timeseries.get_range(
#     dataset="GLBX.MDP3",
#     symbols=["ESM2", "NQZ2"],
#     schema="ohlcv-1s",
#     start="2022-06-06T14:30:00",
#     end="2025-03-15T14:40:00",
# )
#
# data.replay(print)

def rank_by_volume(top=10):
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols="ALL_SYMBOLS",
        schema="ohlcv-1d",
        start="2023-08-15",
        end="2023-08-16",
    )
    df = data.to_df()
    return df.sort_values(by="volume", ascending=False).instrument_id.tolist()[:top]

top_instruments = rank_by_volume()
print(top_instruments)

def get_symbol_properties(instrument_id_list):
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        stype_in="instrument_id",
        symbols=instrument_id_list,
        schema="definition",
        start="2023-08-15",
        end="2023-08-16",
    )
    return data.to_df()[[
        "instrument_id", "raw_symbol",
        "min_price_increment", "match_algorithm", "expiration"
    ]]

print(get_symbol_properties(top_instruments).to_markdown())