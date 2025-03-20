import databento as db

client = db.Historical("db-Gdi8gtVfGJCDUBKxNS8YDKJGuyLAF")
data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    symbols="ALL_SYMBOLS",
    start="2022-06-02T14:20:00",
    end="2022-06-02T14:30:00",
)

data.replay(print)