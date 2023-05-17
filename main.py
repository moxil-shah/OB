import dash
import plotly.graph_objs as go
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from dash_extensions import WebSocket
from dash.exceptions import PreventUpdate
import dash_daq as daq


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


def initHeatMap():
    global BUCKETSIZE, ORDERBOOKSIZE, TRADINGPAIR, PRICELEVELS, MAXCOLUMNS, BOTHSIDES, INTERVAL, heatmapBusy, middle, initial_mode
    BUCKETSIZE = 1
    ORDERBOOKSIZE = 5000
    TRADINGPAIR = "BTCUSDT"
    middle = getPriceOfAssetAdjustedForBucketSize(TRADINGPAIR, BUCKETSIZE)
    obJSON = getOrderBook(TRADINGPAIR, ORDERBOOKSIZE)
    bidsDic, asksDic = sumQuantities(
        obJSON["bids"], obJSON["asks"], BUCKETSIZE)
    BOTHSIDES = max(middle - min(bidsDic), max(asksDic) - middle)
    PRICELEVELS = BOTHSIDES * 2 + 1
    MAXCOLUMNS = 30
    INTERVAL = 4000
    heatmapBusy = False
    initial_mode = 'lines+markers'


app = dash.Dash(__name__)

initHeatMap()

# Set the initial y-axis range
y_min = middle - BOTHSIDES
y_max = middle + BOTHSIDES

# Create an empty heatmap with random values
heatmap = np.full((PRICELEVELS, MAXCOLUMNS), np.nan)
timeArray = np.array([])
x1 = np.empty(0)
y2 = np.empty(0)
bubble_sizes = np.empty(0)

now = datetime.now() - timedelta(seconds=INTERVAL // 1000 * MAXCOLUMNS)
for i in range(MAXCOLUMNS):
    timeArray = np.append(timeArray, now)
    now = now + timedelta(seconds=INTERVAL // 1000)

# Create the trace for the heatmap
heatTrace = go.Heatmap(name='Limit Orders', z=heatmap, x=timeArray, y=np.arange(
    y_min, y_max+1, 1), colorscale='hot')

bubbleTrace = go.Scatter(x=x1, y=y2, mode=initial_mode, name='Volume Profile', line=dict(width=2, color='blue'),
                         marker=dict(size=bubble_sizes,
                                     sizemode='diameter', sizeref=1),
                         hovertemplate="Quantity: %{marker.size:.2f}<br>Price: %{y}<extra></extra>"
                         )

# Create the layout for the heatmap
layout = go.Layout(
    title='Real-Time Order Book',
    xaxis=dict(title='Time'),
    yaxis=dict(title='Price'),
    height=800
)

# Create the figure with the trace and layout
fig = go.Figure(data=[heatTrace, bubbleTrace], layout=layout)
fig['layout']['uirevision'] = 1

# Create the app layout
app.layout = dash.html.Div(children=[
    dash.dcc.Graph(id='realtime-orderbook', figure=fig),
    dash.dcc.Interval(id='interval-component',
                      interval=INTERVAL, n_intervals=0),
    dash.dcc.RadioItems(
        id='mode-switch',
        options=[
            {'label': 'Lines', 'value': 'lines'},
            {'label': 'Markers', 'value': 'markers'},
            {'label': 'Lines+Markers', 'value': 'lines+markers'}
        ],
        value=initial_mode
    ), dash.dcc.Slider(min=0, max=5, step=0.1, value=1,
                       id='bubble-size-slider'
                       ), WebSocket(url=f"wss://stream.binance.com:9443/ws/{TRADINGPAIR.lower()}@trade", id="wsMarketOrders"),])


@app.callback(
    dash.dependencies.Output('realtime-orderbook', 'figure'),
    dash.dependencies.Input('interval-component', 'n_intervals'),
    dash.dependencies.Input('mode-switch', 'value'),
    dash.dependencies.Input('bubble-size-slider', 'value'),
    dash.dependencies.Input("wsMarketOrders", "message"),
    prevent_initial_call=True
)
def update_heatmap(n, modeValue, sliderValue, e):
    global y_min, y_max, heatmap, timeArray, x1, y2, bubble_sizes, heatmapBusy
    triggered_id = dash.ctx.triggered_id
    if triggered_id == "mode-switch":
        fig['data'][1].mode = modeValue
    elif triggered_id == "bubble-size-slider":
        fig['data'][1].marker["sizeref"] = sliderValue
    elif triggered_id == "interval-component":
        if heatmapBusy:
            print("heatmap busy")
            return fig
        heatmapBusy = True
        # Generate new column of heatmap data
        middle = getPriceOfAssetAdjustedForBucketSize(TRADINGPAIR, BUCKETSIZE)
        obJSON = getOrderBook(TRADINGPAIR, ORDERBOOKSIZE)
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
        timeArray = np.append(timeArray[1:], datetime.now())
        # Update the heatmap trace with the new data and y-axis range
        fig.data[0].update(z=heatmap, x=timeArray,
                           y=np.arange(y_min_new, y_max_new+1, 1))

        # Store the updated y-axis range for the next update
        y_min = y_min_new
        y_max = y_max_new

        heatmapBusy = False
    elif triggered_id == "wsMarketOrders":
        jsonData = e.get('data')
        if jsonData:
            jsonData = json.loads(jsonData)
        else:
            return fig

        current_time = datetime.fromtimestamp(int(jsonData["T"]) / 1000)

        if len(x1) and current_time == x1[-1]:
            # Add 1 millisecond to the current time
            current_time += timedelta(milliseconds=1)
        x1 = np.append(x1,  current_time)
        y2 = np.append(y2, float(jsonData['p']))
        bubble_sizes = np.append(bubble_sizes, 10 * float(jsonData['q']))

        # Change bubble color based on the value of jsonData['w']
        colors = np.where(jsonData['m'] is True,
                          'rgb(255, 0, 0)', 'rgb(0, 255, 0)')
        if fig['data'][1]['marker']['color'] is None:
            fig['data'][1]['marker']['color'] = []
        new_colors = np.append(fig['data'][1]['marker']['color'], colors)

        while len(x1) > 0 and x1[0] < timeArray[0]:
            x1 = np.delete(x1, 0)
            y2 = np.delete(y2, 0)
            bubble_sizes = np.delete(bubble_sizes, 0)
            new_colors = np.delete(new_colors, 0)

        # Update the size and sizemode of the marker of the bubble chart trace
        fig['data'][1]['x'] = x1
        fig['data'][1]['marker']['size'] = bubble_sizes
        fig['data'][1]['y'] = y2
        fig['data'][1]['marker']['color'] = new_colors  # Update bubble colors

    # Return the updated figure
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
