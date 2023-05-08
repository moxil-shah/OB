import plotly.graph_objs as go
import numpy as np
import json
import dash
from dash import dcc
from dash import html
from dash_extensions import WebSocket
from dash_extensions.enrich import Input, Output

# Generate some random data
x = np.empty(0)
y1 = np.empty(0)
y2 = np.empty(0)
bubble_sizes = np.empty(0)

# Create the line chart trace
trace1 = go.Scatter(x=x, y=y1, mode='lines', name='Line Chart')

# Create the bubble chart trace
trace2 = go.Scatter(x=x, y=y2, mode='markers', name='Bubble Chart', 
                    marker=dict(size=bubble_sizes, sizemode='diameter', sizeref=1))

# Create the layout
layout = go.Layout(title='Bubble Chart over Line Chart', 
                   xaxis=dict(title='X-Axis'), yaxis=dict(title='Y-Axis'))

# Create the figure
fig = go.Figure(data=[trace1, trace2], layout=layout)

# Create the app and the layout
app = dash.Dash(__name__)
app.layout = html.Div([dcc.Graph(id='realtimeMarketOrders', figure=fig), 
                       WebSocket(url="wss://stream.binance.com:9443/ws/ethusdt@trade", id="wsMarketOrders")])

@app.callback(Output("realtimeMarketOrders", "figure"), [Input("wsMarketOrders", "message")])
def message(e):
    global x, y1, y2, bubble_sizes
    jsonData = None
    if e is not None:
        jsonData = json.loads(e['data'])
    if jsonData is None:
        return fig
    x = np.append(x,  len(x) + 1)
    y1 = np.append(y1, float(jsonData['p']))
    y2 = np.append(y2, float(jsonData['p']))
    bubble_sizes = np.append(bubble_sizes, float(jsonData['q']))
    print(max(bubble_sizes))
    # Update the x and y data of the line chart trace
    fig['data'][0]['x'] = x
    fig['data'][0]['y'] = y1
    
    # Update the size and sizemode of the marker of the bubble chart trace
    
    fig['data'][1]['x'] = x
    fig['data'][1]['marker']['size'] = bubble_sizes
    fig['data'][1]['y'] = y2
    
    # Create a new figure object with the updated trace data and layout
    ## new_fig = go.Figure(data=fig['data'], layout=fig['layout'])
    # Check if the callback was triggered by the websocket event or by the initial page load
    # ctx = dash.callback_context
    fig.update_layout(uirevision=1) 
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
