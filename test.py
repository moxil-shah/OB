import threading
import websocket
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import time
# Global flag to control the WebSocket thread
ws = None

# Function to handle the WebSocket connection and print received messages
def wsrun(uri):
    global ws
    ws = websocket.WebSocketApp(uri, on_message=on_message)
    ws.run_forever()


def on_message(ws, message):
    print(message)

# Define the Dash app
app = dash.Dash(__name__)

# Define the available WebSocket endpoints
endpoints = {
    'ETH/USDT': 'wss://stream.binance.com:9443/ws/ethusdt@trade',
    'BTC/USDT': 'wss://stream.binance.com:9443/ws/btcusdt@trade'
}

# Define the layout of the app
app.layout = html.Div([
    html.H1('WebSocket Endpoint Selector'),
    dcc.Dropdown(
        id='endpoint-dropdown',
        options=[{'label': symbol, 'value': uri} for symbol, uri in endpoints.items()],
        value=list(endpoints.values())[0]  # Set the default value to the first endpoint
    ),
    html.Div(id='output')
])

# Callback to update the WebSocket connection when the dropdown value changes
@app.callback(Output('output', 'children'), [Input('endpoint-dropdown', 'value')])
def update_websocket(uri):
    if uri is None:
        raise PreventUpdate
    else:
        ws.close()
    websocket_thread = threading.Thread(target=wsrun, args=(uri,), name='websocket_thread')
    websocket_thread.start()

    return f"Connected to {uri}"

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
