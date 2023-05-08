from dash_extensions.enrich import DashProxy, html, dcc, Input, Output
from dash_extensions import WebSocket

# Create example app.
app = DashProxy(__name__)
app.layout = html.Div([
    dcc.Input(id="input", autoComplete="off"),
    html.Div(id="message"),
    WebSocket(url="wss://stream.binance.com:9443/ws/ethusdt@trade", id="wsMarketOrders")
])



@app.callback(Output("message", "children"), [Input("wsMarketOrders", "message")])
def message(e):
    return f"Response from websocket: {e['data']}"

if __name__ == '__main__':
    app.run_server()
