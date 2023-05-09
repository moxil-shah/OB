import plotly.graph_objs as go
import numpy as np
import json
import dash
from dash import dcc
from dash import html
from dash_extensions import WebSocket
from dash_extensions.enrich import Input, Output
from datetime import datetime, timedelta


# Generate some random data
x = np.empty(0)
y1 = np.empty(0)
y2 = np.empty(0)
bubble_sizes = np.empty(0)

# Create the line chart trace
trace1 = go.Scatter(x=x, y=y1, mode='lines', name='Price', line=dict(width=1))

# Create the bubble chart trace
trace2 = go.Scatter(x=x, y=y2, mode='markers', name='Volume Profile',
                    marker=dict(size=bubble_sizes,
                                sizemode='diameter', sizeref=1),
                    hovertemplate="Quantity: %{marker.size:.2f}<br>Price: %{y}<extra></extra>"
                    )

# Create the layout
layout = go.Layout(title='ETH/USDT Order Book Insight',
                   xaxis=dict(title='Time'), yaxis=dict(title='ETH/USDT'))

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

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    
    if len(x) and current_time == x[-1]:
        # Add 1 millisecond to the current time
        current_time = (now + timedelta(milliseconds=1)).strftime("%H:%M:%S.%f")  
    x = np.append(x,  current_time)
    y1 = np.append(y1, float(jsonData['p']))
    y2 = np.append(y2, float(jsonData['p']))
    bubble_sizes = np.append(bubble_sizes, 10 * float(jsonData['q']))

    # Change bubble color based on the value of jsonData['w']
    colors = np.where(jsonData['m'] is True,
                      'rgb(255, 0, 0)', 'rgb(0, 255, 0)')
    if fig['data'][1]['marker']['color'] is None:
        fig['data'][1]['marker']['color'] = []
    new_colors = np.append(fig['data'][1]['marker']['color'], colors)

    # Remove the leftmost data point if there are more than 100 data points
    limit = 200
    if len(x) > limit:
        x = x[-limit:]
        y1 = y1[-limit:]
        y2 = y2[-limit:]
        bubble_sizes = bubble_sizes[-limit:]
        new_colors = new_colors[-limit:]

    # Update the x and y data of the line chart trace
    fig['data'][0]['x'] = x
    fig['data'][0]['y'] = y1

    # Update the size and sizemode of the marker of the bubble chart trace
    fig['data'][1]['x'] = x
    fig['data'][1]['marker']['size'] = bubble_sizes
    fig['data'][1]['y'] = y2
    fig['data'][1]['marker']['color'] = new_colors  # Update bubble colors

    # Create a new figure object with the updated trace data and layout
    fig.update_layout(uirevision=1)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
