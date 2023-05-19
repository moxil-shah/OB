import requests

def getOrderBook(symbol, limit):
    url = f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}'
    response = requests.get(url, verify=False)
    response.raise_for_status()  # Check for request failure and raise an exception if needed
    response_json = response.json()
    if "bids" not in response_json or "asks" not in response_json:
        raise Exception("Orderbook request failed")
    return response_json

while True:
    print(getOrderBook("ETHUSDT", 5000))
    