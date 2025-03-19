import requests
import pandas as pd

API_KEY = '_gDUH1xTONS4LP_ao38ZUEe9Wox71CoDFr_6p2'
BASE_URL = 'https://api.polygon.io'

def get_histdata_polygon(ticker, start_date, end_date, timespan, multiplier):

    url = f"{BASE_URL}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_date}/{end_date}?apiKey={API_KEY}"

    response = requests.get(url)

    if response.status_code == 200:

        data = response.json()
        df = pd.DataFrame(data['results'])

        # convert timestamp to datetime format
        df['timestamp'] = pd.to_datetime(df['t'], unit='ms')

        # organize df columns
        columns = ['timestamp', 'o', 'h', 'l', 'c', 'v']
        df = df[columns]
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df.set_index('timestamp', inplace=True)

        return df

    elif response.status_code == 403:
        print("Error 403: Forbidden. Check your API key and subscription plan.")
    else:
        print(f"Error: {response.status_code} - {response.text}")

    return pd.DataFrame()