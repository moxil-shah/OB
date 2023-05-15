import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Input(id='input', value='initial value', type='text'),
    html.Div(id='output')
])


@app.callback(
    dash.dependencies.Output('output', 'children'),
    dash.dependencies.Input('input', 'value'),
)
def update_output(value):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    previous_triggered_id = ctx.previous_triggered[0]['prop_id'].split('.')[0] if ctx.previous_triggered else None
    return f'Triggered by {triggered_id}. Previous triggered by {previous_triggered_id}.'


if __name__ == '__main__':
    app.run_server(debug=True)
