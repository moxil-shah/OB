import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
import numpy as np
import requests
import json


def getOrderBook(symbol, limit):
    response = requests.get(
        f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}')
    #print(response)
    return response.json()


def getPriceOfAssetAdjustedForBucketSize(symbol, bucket_size):
    response = requests.get(
        f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
    response = response.json()
    #print(response)
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


# Initialize the app
app = dash.Dash(__name__)
bucketSize = 1

middle = getPriceOfAssetAdjustedForBucketSize("ETHUSDT", bucketSize)
obJSON = getOrderBook("ETHUSDT", 5000)
bidsDic, asksDic = sumQuantities(obJSON["bids"], obJSON["asks"], bucketSize)
bidsPricesList = list(bidsDic.keys())
asksPricesList = list(asksDic.keys())
bidsPricesList.sort()
asksPricesList.sort()

# Set the initial y-axis range
y_min = bidsPricesList[-51]
y_max = asksPricesList[50]


# Create an empty heatmap with random values
heatmap = np.full((101, 100), np.nan)
initColumn = np.array([])
for bidPrice in range(y_min, middle):
    initColumn = np.append(initColumn, bidsDic[bidPrice])
initColumn = np.append(initColumn, bidsDic[middle] + asksDic[middle])
for askPrice in range(middle + 1, y_max + 1):
    initColumn = np.append(initColumn, asksDic[askPrice])
# Replace the last column of the array with the custom column
heatmap[:, -1] = initColumn
# Create the trace for the heatmap
trace = go.Heatmap(z=heatmap, y=np.arange(y_min, y_max+1, 1), colorscale='hot')

# Create the layout for the heatmap
layout = go.Layout(
    title='Real-Time Order Book',
    xaxis=dict(title='X Axis'),
    yaxis=dict(title='Price'),
    height=700
)

# Create the figure with the trace and layout
fig = go.Figure(data=[trace], layout=layout)

# Create the app layout
app.layout = html.Div(children=[
    dcc.Graph(id='realtime-orderbook', figure=fig),
    dcc.Interval(id='interval-component', interval=3000, n_intervals=0)
])

# Define the callback function to update the heatmap


@app.callback(
    dash.dependencies.Output('realtime-orderbook', 'figure'),
    [dash.dependencies.Input('interval-component', 'n_intervals')],
    prevent_initial_call=True
)
def update_heatmap(n):
    global y_min, y_max, heatmap
    # Generate new column of heatmap data
    middle = getPriceOfAssetAdjustedForBucketSize("ETHUSDT", bucketSize)
    obJSON = getOrderBook("ETHUSDT", 5000)
    bidsDic, asksDic = sumQuantities(
        obJSON["bids"], obJSON["asks"], bucketSize)
    bidsPricesList = list(bidsDic.keys())
    asksPricesList = list(asksDic.keys())
    bidsPricesList.sort()
    asksPricesList.sort()

    # Set the initial y-axis range
    y_min_new = bidsPricesList[-51]
    y_max_new = asksPricesList[50]

    if y_max_new > y_max:
        shiftUp = y_max_new - y_max

        heatmap = heatmap[shiftUp:, :]
        print(heatmap.shape)
        n = shiftUp
        # create a 2D array of NaN values with n rows and the same number of columns as the heatmap
        nan_rows = np.full((n, heatmap.shape[1]), np.nan)
        # concatenate the NaN rows with the heatmap along the row axis
        heatmap = np.concatenate((heatmap, nan_rows), axis=0)
        print(heatmap.shape)
        print(shiftUp, "shiftup")
    elif y_max_new < y_max:
        shiftDown = y_max - y_max_new
        heatmap = heatmap[:-shiftDown, :]
        print(heatmap.shape)
        n = shiftDown
        # create a 2D array of NaN values with n rows and the same number of columns as the heatmap
        nan_rows = np.full((n, heatmap.shape[1]), np.nan)
        # concatenate the NaN rows with the heatmap along the row axis
        heatmap = np.concatenate((nan_rows, heatmap), axis=0)
        print(heatmap.shape)
        print(shiftDown, "shiftdown")

    new_col = np.array([])
    for bidPrice in range(y_min_new, middle):
        new_col = np.append(new_col, bidsDic[bidPrice])
    middleVal = 0
    if middle in bidsDic:
        middleVal += bidsDic[middle]
    if middle in asksDic:
        middleVal += asksDic[middle]
    new_col = np.append(new_col, middleVal)
    for askPrice in range(middle + 1, y_max_new + 1):
        new_col = np.append(new_col, asksDic[askPrice])
    new_col = new_col.reshape((len(new_col), 1))
    if y_max_new > y_max:
        print(len(new_col))
    # Add new column to existing heatmap data
    heatmap = np.concatenate((heatmap, new_col), axis=1)

    # Check if heatmap has more than 100 columns
    if heatmap.shape[1] > 100:

        # Delete the leftmost column of heatmap data
        heatmap = heatmap[:, 1:]

    # Update the heatmap trace with the new data and y-axis range
    fig.data[0].update(z=heatmap, y=np.arange(y_min_new, y_max_new+1, 1))

    # Store the updated y-axis range for the next update
    y_min = y_min_new
    y_max = y_max_new

    # Return the updated figure
    fig.update_layout(uirevision=1)
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
