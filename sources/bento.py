import databento as db
import local.api_keys as keys

# request network data synchronous!
client = db.Historical(keys.bento_api_key)

def nq():
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["NQ.v.0"],
        stype_in="continuous",
        schema="ohlcv-1m",
        start="2023-01-01",
        end="2025-03-15",
    )
    return data.to_df()

print(nq().to_markdown())