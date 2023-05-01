import requests
import json

def getOrderBook(symbol, limit):
    response = requests.get(f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}')
    return response.json()

def getPriceOfAssetAdjustedForBucketSize(symbol, bucket_size):
    response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
    response = response.json()
    price = int(float(response["price"]) / bucket_size) * bucket_size
    return price

def sumQuantities(bids, asks, bucket_size):
    # Create empty dictionaries for bids and asks
    bid_buckets = {}
    ask_buckets = {}

    # Loop through each bid and ask
    for bid in bids:
        price, quantity = bid
        # Calculate which bucket this price belongs to
        bucket_price = int(float(price) / bucket_size) * bucket_size
        # Add this quantity to the appropriate bucket
        if bucket_price in bid_buckets:
            bid_buckets[bucket_price] += float(quantity)
        else:
            bid_buckets[bucket_price] = float(quantity)

    for ask in asks:
        price, quantity = ask
        # Calculate which bucket this price belongs to
        bucket_price = int(float(price) / bucket_size) * bucket_size
        # Add this quantity to the appropriate bucket
        if bucket_price in ask_buckets:
            ask_buckets[bucket_price] += float(quantity)
        else:
            ask_buckets[bucket_price] = float(quantity)

    return bid_buckets, ask_buckets


data = getOrderBook('ETHUSDT', 5000)
print(getPriceOfAssetAdjustedForBucketSize("ETHUSDT", 10))