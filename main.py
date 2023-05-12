import dash
import plotly.graph_objs as go
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from dash_extensions import WebSocket


def getOrderBook(symbol, limit):
    response = requests.get(
        f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}')
    # print(response)
    return response.json()


def getPriceOfAssetAdjustedForBucketSize(symbol, bucket_size):
    response = requests.get(
        f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
    response = response.json()
    # print(response)
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


def getColumns(y_min, middle, y_max, bidsDic, asksDic):
    initColumn = np.array([])
    for bidPrice in range(y_min, middle):
        if bidPrice in bidsDic:
            initColumn = np.append(initColumn, bidsDic[bidPrice])
        else:
            initColumn = np.append(initColumn, np.nan)
    middleVal = 0
    if middle in bidsDic:
        middleVal += bidsDic[middle]
    if middle in asksDic:
        middleVal += asksDic[middle]
    initColumn = np.append(initColumn, middleVal)
    for askPrice in range(middle + 1, y_max + 1):
        if askPrice in asksDic:
            initColumn = np.append(initColumn, asksDic[askPrice])
        else:
            initColumn = np.append(initColumn, np.nan)
    return initColumn


# Initialize the app
app = dash.Dash(__name__)
BUCKETSIZE = 1
ORDERBOOKSIZE = 5000
PRICELEVELS = 201
MAXCOLUMNS = 100
BOTHSIDES = 100
INTERVAL = 3000
middle = getPriceOfAssetAdjustedForBucketSize("ETHUSDT", BUCKETSIZE)

# Set the initial y-axis range
y_min = middle - BOTHSIDES
y_max = middle + BOTHSIDES

# Create an empty heatmap with random values
heatmap = np.full((PRICELEVELS, MAXCOLUMNS), np.nan)

timeArray = np.array([])
now = datetime.now() - timedelta(seconds=INTERVAL // 1000 * MAXCOLUMNS)
for i in range(MAXCOLUMNS):
    timeArray = np.append(timeArray, now)
    now = now + timedelta(seconds=INTERVAL // 1000)

# Create the trace for the heatmap
trace = go.Heatmap(z=heatmap, x=timeArray, y=np.arange(
    y_min, y_max+1, 1), colorscale='hot')

# Create the layout for the heatmap
layout = go.Layout(
    title='Real-Time Order Book',
    xaxis=dict(title='Time'),
    yaxis=dict(title='Price'),
    height=800
)

x1 = np.empty(0)
y1 = np.empty(0)
priceTrace = go.Scatter(x=x1, y=y1, mode='lines', name='Price',  line=dict(width=1, color='white'))

# Create the figure with the trace and layout
fig = go.Figure(data=[trace, priceTrace], layout=layout)
fig['layout']['uirevision'] = 1

# Create the app layout
app.layout = dash.html.Div(children=[
    dash.dcc.Graph(id='realtime-orderbook', figure=fig),
    dash.dcc.Interval(id='interval-component', interval=INTERVAL, n_intervals=0),
    WebSocket(url="wss://stream.binance.com:9443/ws/ethusdt@trade", id="wsMarketOrders")])

@app.callback(
    dash.dependencies.Output('realtime-orderbook', 'figure'),
    dash.dependencies.Input('interval-component', 'n_intervals'),
    dash.dependencies.Input("wsMarketOrders", "message"),
    prevent_initial_call=True
)
def update_heatmap(n, e):
    global y_min, y_max, heatmap, timeArray, x1, y1
    triggered_id = dash.ctx.triggered_id
    if triggered_id == "interval-component":
        # Generate new column of heatmap data
        middle = getPriceOfAssetAdjustedForBucketSize("ETHUSDT", BUCKETSIZE)
        obJSON = getOrderBook("ETHUSDT", ORDERBOOKSIZE)
        bidsDic, asksDic = sumQuantities(
            obJSON["bids"], obJSON["asks"], BUCKETSIZE)

        # Set the initial y-axis range
        y_min_new = middle - BOTHSIDES
        y_max_new = middle + BOTHSIDES

        if y_max_new > y_max:
            shiftUp = y_max_new - y_max

            heatmap = heatmap[shiftUp:, :]
            # create a 2D array of NaN values with n rows and the same number of columns as the heatmap
            nan_rows = np.full((shiftUp, heatmap.shape[1]), np.nan)
            # concatenate the NaN rows with the heatmap along the row axis
            heatmap = np.concatenate((heatmap, nan_rows), axis=0)
        elif y_max_new < y_max:
            shiftDown = y_max - y_max_new
            heatmap = heatmap[:-shiftDown, :]
            # create a 2D array of NaN values with n rows and the same number of columns as the heatmap
            nan_rows = np.full((shiftDown, heatmap.shape[1]), np.nan)
            # concatenate the NaN rows with the heatmap along the row axis
            heatmap = np.concatenate((nan_rows, heatmap), axis=0)

        new_col = getColumns(y_min_new, middle, y_max_new, bidsDic, asksDic)

        new_col = new_col.reshape((len(new_col), 1))

        # Add new column to existing heatmap data
        heatmap = np.concatenate((heatmap, new_col), axis=1)

        # Delete the leftmost column of heatmap data
        heatmap = heatmap[:, 1:]
        timeArray = timeArray[1:]
        timeArray = np.append(timeArray, datetime.now())
        # Update the heatmap trace with the new data and y-axis range
        fig.data[0].update(z=heatmap, x=timeArray,
                        y=np.arange(y_min_new, y_max_new+1, 1))

        # Store the updated y-axis range for the next update
        y_min = y_min_new
        y_max = y_max_new


    elif triggered_id == "wsMarketOrders":
        jsonData = None
        if e is not None:
            jsonData = json.loads(e['data'])
        if jsonData is None:
            return fig

        current_time = datetime.now()
       
        if len(x1) and current_time == x1[-1]:
            print('bruh')
            # Add 1 millisecond to the current time
            current_time += timedelta(milliseconds=1)
        x1 = np.append(x1,  current_time)
        y1 = np.append(y1, float(jsonData['p']))
        
        while len(x1) > 0 and x1[0] < timeArray[0]:
            x1 = np.delete(x1, 0)
            y1 = np.delete(y1, 0)

        # Update the x and y data of the line chart trace
        fig['data'][1]['x'] = x1
        fig['data'][1]['y'] = y1
        
    # Return the updated figure
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
