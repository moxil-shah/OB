from dash import Dash, dcc, html, ctx
import plotly.graph_objects as go
import numpy as np
import websocket
import _thread
import time
import rel
import json
import os
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# Set up the Dash app
app = Dash(__name__)
creds = service_account.Credentials.from_service_account_file(
    'order-book-heatmap-61965d32f961.json',
    scopes=["https://www.googleapis.com/auth/bigquery"]
)

client = bigquery.Client(
    project="order-book-heatmap",
    credentials=creds
)

# Get a reference to the target table
dataset_id = 'Trades'
table_id = 'OrderBookUpdates'
table_ref = client.dataset(dataset_id).table(table_id)


# Define the input parameters for the stored procedure
bucket_size = 1000 * 60 * 60 * 1 # Example value, modify as needed
start_time = 0  # Example value, modify as needed
end_time = int(time.time() * 1000)  # current time

# Call the stored procedure
query = f"CALL `order-book-heatmap.Trades.CalculateCvd`({bucket_size}, {start_time}, {end_time})"
query_job = client.query(query)
results = query_job.result()
df = results.to_dataframe()

# Create the plot
fig = go.Figure(data=go.Scatter(x=df['TimeBucket'], y=df['CVD'], mode='lines'))

# Set plot layout
fig.update_layout(
    title='CVD Of BTCUSDT',
    xaxis_title='Time',
    yaxis_title='CVD in BTC'
)

# Set up Dash layout
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
