import databento as db

# todo need to constantly create new api key on free tier
client = db.Historical("db-hRKYNXiVSbaw9FPMFJwdjyjrG63pi")

# data = client.timeseries.get_range(
#     dataset="GLBX.MDP3",
#     symbols=["ESM2", "NQZ2"],
#     schema="ohlcv-1s",
#     start="2022-06-06T14:30:00",
#     end="2025-03-15T14:40:00",
# )
#
# data.replay(print)
#
# def rank_by_volume(top=10):
#     data = client.timeseries.get_range(
#         dataset="GLBX.MDP3",
#         symbols="ALL_SYMBOLS",
#         schema="ohlcv-1d",
#         start="2023-08-15",
#         end="2023-08-16",
#     )
#     df = data.to_df()
#     return df.sort_values(by="volume", ascending=False).instrument_id.tolist()[:top]
#
# top_instruments = rank_by_volume()
# print(top_instruments)
#
# def get_symbol_properties(instrument_id_list):
#     data = client.timeseries.get_range(
#         dataset="GLBX.MDP3",
#         stype_in="instrument_id",
#         symbols=instrument_id_list,
#         schema="definition",
#         start="2023-08-15",
#         end="2023-08-16",
#     )
#     return data.to_df()[[
#         "instrument_id", "raw_symbol",
#         "min_price_increment", "match_algorithm", "expiration"
#     ]]
#
# print(get_symbol_properties(top_instruments).to_markdown())

def nq():
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["NQ.c.0"],
        stype_in="continuous",
        schema="ohlcv-1m",
        start="2023-01-01",
        end="2025-03-15",
    )
    return data.to_df()

print(nq().to_markdown())