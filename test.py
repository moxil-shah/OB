import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
import numpy as np
import requests
import json

def getOrderBook(symbol, limit):
    response = requests.get(f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}')
    return response.json()

def sum_quantities(bids, asks, bucket_size):
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

# Set the initial y-axis range
y_min = 1900
y_max = 2100

# Create an empty heatmap with random values
heatmap = np.full((100, 100), np.nan)
# Create the trace for the heatmap
trace = go.Heatmap(z=heatmap, y=np.arange(y_min, y_max+1, 1), colorscale='hot')

# Create the layout for the heatmap
layout = go.Layout(
    title='Real-Time Order Book',
    xaxis=dict(title='X Axis'),
    yaxis=dict(title='Price')
)

# Create the figure with the trace and layout
fig = go.Figure(data=[trace], layout=layout)

# Create the app layout
app.layout = html.Div(children=[
    dcc.Graph(id='realtime-orderbook', figure=fig),
    dcc.Interval(id='interval-component', interval=100, n_intervals=0)
])

# Define the callback function to update the heatmap
@app.callback(
    dash.dependencies.Output('realtime-orderbook', 'figure'),
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_heatmap(n):
    global y_min, y_max, heatmap
    # Generate new column of heatmap data
    new_col = np.random.randint(low=y_min, high=y_max+1, size=(100, 1))

    # Add new column to existing heatmap data
    heatmap = np.concatenate((heatmap, new_col), axis=1)

    # Check if heatmap has more than 100 columns
    if heatmap.shape[1] > 100:
        
        # Delete the leftmost column of heatmap data
        heatmap = heatmap[:, 1:]

    # Calculate the new minimum and maximum values of the y-axis
    y_min_new = np.nanmin(heatmap)
    y_max_new = np.nanmax(heatmap)
    
    # Adjust the y-axis range to keep a fixed 50-unit gap between the minimum and maximum values
    if y_max_new - y_min_new < 50:
        y_min_new = y_max_new - 50
    
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
