import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np

# Create the app layout
app = dash.Dash(__name__)

# Set up some sample data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# Initial mode and trace
initial_mode = 'lines'
trace = go.Scatter(x=x, y=y1, mode=initial_mode, name='Trace')

# Define the app layout
app.layout = html.Div([
    dcc.Graph(id='graph', figure={'data': [trace]}),
    dcc.RadioItems(
        id='mode-switch',
        options=[
            {'label': 'Lines', 'value': 'lines'},
            {'label': 'Markers', 'value': 'markers'},
            {'label': 'Lines+Markers', 'value': 'lines+markers'}
        ],
        value=initial_mode
    )
])

# Define the callback to update the trace mode
@app.callback(
    Output('graph', 'figure'),
    Input('mode-switch', 'value')
)
def update_trace_mode(mode):
    trace.mode = mode
    return {'data': [trace]}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
