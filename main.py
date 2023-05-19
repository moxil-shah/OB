import numpy as np
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta
from dash import Dash, dcc, html, ctx
from dash.dependencies import Input, Output

VERIFY = True
BUCKETSIZE = 1


def getOrderBook(symbol, limit):
    url = f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}'
    response = requests.get(url, verify=VERIFY)
    # Check for request failure and raise an exception if needed
    response.raise_for_status()
    response_json = response.json()
    return response_json


def getPriceOfAssetAdjustedForBucketSize(symbol, bucket_size):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    response = requests.get(url, verify=VERIFY)
    # Check for request failure and raise an exception if needed
    response.raise_for_status()
    response_json = response.json()
    price = float(response_json["price"])
    adjusted_price = int(price / bucket_size) * bucket_size
    return adjusted_price


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


def initHeatMap(symbol):
    global g_orderBookSize, g_tradingPair, g_priceLevels, g_maxColumns, g_bothSides, g_intervals, g_initialMode
    g_orderBookSize = 1000
    g_tradingPair = symbol
    middle = getPriceOfAssetAdjustedForBucketSize(g_tradingPair, BUCKETSIZE)
    obJSON = getOrderBook(g_tradingPair, g_orderBookSize)
    bidsDic, asksDic = sumQuantities(
        obJSON["bids"], obJSON["asks"], BUCKETSIZE)
    g_bothSides = max(middle - min(bidsDic), max(asksDic) - middle)
    g_priceLevels = g_bothSides * 2 + 1
    g_maxColumns = 100
    g_intervals = 1000
    g_initialMode = 'lines+markers'
    return middle - g_bothSides, middle + g_bothSides


def padTimeArray():
    global g_timeArray, g_intervals, g_maxColumns
    now = datetime.now() - timedelta(seconds=g_intervals // 1000 * g_maxColumns)
    for i in range(g_maxColumns):
        g_timeArray = np.append(g_timeArray, now)
        now = now + timedelta(seconds=g_intervals // 1000)


app = Dash(__name__)
app.prevent_initial_callbacks = False

# Set the initial y-axis range
g_yMin, g_yMax = initHeatMap("ETHUSDT")

# Create an empty heatmap
g_heatmap = np.full((g_priceLevels, g_maxColumns), np.nan)
g_timeArray = np.array([])
g_bestBidX = np.empty(0)
g_bestBidY = np.empty(0)
g_bestAskX = np.empty(0)
g_bestAskY = np.empty(0)

padTimeArray()

# Create the trace for the heatmap
heatTrace = go.Heatmap(name='Limit Orders', z=g_heatmap, x=g_timeArray, y=np.arange(
    g_yMin, g_yMax+1, 1), colorscale='Cividis')

bestBidTrace = go.Scatter(x=g_bestBidX, y=g_bestBidY, mode=g_initialMode,
                          name='Best Bid Trace', line=dict(width=1, color='green'))
bestAskTrace = go.Scatter(x=g_bestAskX, y=g_bestAskY, mode=g_initialMode,
                          name='Best Ask Trace', line=dict(width=1, color='red'))

# Create the layout for the heatmap
layout = go.Layout(
    title=f'Real-Time Order Book for {g_tradingPair}',
    xaxis=dict(title='Time'),
    yaxis=dict(title='Price'),
    height=800
)

# Create the figure with the trace and layout
fig = go.Figure(data=[heatTrace, bestBidTrace, bestAskTrace], layout=layout)
fig['layout']['uirevision'] = 1

# Create the app layout
app.layout = html.Div(children=[
    dcc.Dropdown(['BTCUSDT', 'ETHUSDT'],
                 'ETHUSDT', id='pair-dropdown'),
    dcc.Interval(id='interval-component',
                 interval=g_intervals, n_intervals=0),
    dcc.RadioItems(
        id='mode-switch',
        options=[
            {'label': 'Lines', 'value': 'lines'},
            {'label': 'Markers', 'value': 'markers'},
            {'label': 'Lines+Markers', 'value': 'lines+markers'}
        ],
        value=g_initialMode
    ),
    dcc.Graph(id='realtime-orderbook', figure=fig)])


@app.callback(
    Output('realtime-orderbook', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('mode-switch', 'value'),
)
def update_heatmap(n, modeValue):
    global g_yMin, g_yMax, g_heatmap, g_timeArray, g_bestBidX, g_bestBidY, g_bestAskX, g_bestAskY, g_orderBookSize
    triggered_id = ctx.triggered_id

    if triggered_id == "mode-switch":
        fig['data'][1].mode = modeValue

    elif triggered_id == "interval-component":
        columnTime = datetime.now()
        try:
            middle = getPriceOfAssetAdjustedForBucketSize(
                g_tradingPair, BUCKETSIZE)
            obJSON = getOrderBook(g_tradingPair, g_orderBookSize)
            bestBid = obJSON["bids"][0][0]
            bestAsk = obJSON["asks"][0][0]
        except Exception as e:
            print("Error: ", e)
            return fig
        else:
            bidsDic, asksDic = sumQuantities(
                obJSON["bids"], obJSON["asks"], BUCKETSIZE)

        # Set the initial y-axis range
        yMinNew = middle - g_bothSides
        yMaxNew = middle + g_bothSides

        if yMaxNew > g_yMax:
            shiftUp = yMaxNew - g_yMax
            g_heatmap = g_heatmap[shiftUp:, :]
            # create a 2D array of NaN values with n rows and the same number of columns as the heatmap
            nan_rows = np.full((shiftUp, g_heatmap.shape[1]), np.nan)
            # concatenate the NaN rows with the heatmap along the row axis
            g_heatmap = np.concatenate((g_heatmap, nan_rows), axis=0)
        elif yMaxNew < g_yMax:
            shiftDown = g_yMax - yMaxNew
            g_heatmap = g_heatmap[:-shiftDown, :]
            # create a 2D array of NaN values with n rows and the same number of columns as the heatmap
            nan_rows = np.full((shiftDown, g_heatmap.shape[1]), np.nan)
            # concatenate the NaN rows with the heatmap along the row axis
            g_heatmap = np.concatenate((nan_rows, g_heatmap), axis=0)

        # Generate new column of heatmap data
        new_col = getColumns(yMinNew, middle, yMaxNew, bidsDic, asksDic)
        new_col = new_col.reshape((len(new_col), 1))

        # Add new column to existing heatmap data
        g_heatmap = np.concatenate((g_heatmap, new_col), axis=1)

        g_bestBidX = np.append(g_bestBidX,  columnTime)
        g_bestBidY = np.append(g_bestBidY, bestBid)
        g_bestAskX = np.append(g_bestAskX,  columnTime)
        g_bestAskY = np.append(g_bestAskY, bestAsk)
        # Delete the leftmost column of heatmap data
        g_heatmap = g_heatmap[:, 1:]

        if len(g_bestBidX) > g_maxColumns:
            g_bestBidX = np.delete(g_bestBidX, 0)
            g_bestBidY = np.delete(g_bestBidY, 0)
        if len(g_bestAskX) > g_maxColumns:
            g_bestAskX = np.delete(g_bestAskX, 0)
            g_bestAskY = np.delete(g_bestAskY, 0)

        g_timeArray = np.append(g_timeArray[1:], columnTime)
        # Update the heatmap trace with the new data and y-axis range
        fig.data[0].update(z=g_heatmap, x=g_timeArray,
                           y=np.arange(yMinNew, yMaxNew+1, 1))
        fig['data'][1]['x'] = g_bestBidX
        fig['data'][1]['y'] = g_bestBidY
        fig['data'][2]['x'] = g_bestAskX
        fig['data'][2]['y'] = g_bestAskY

        # Store the updated y-axis range for the next update
        g_yMin = yMinNew
        g_yMax = yMaxNew

    # Return the updated figure
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
