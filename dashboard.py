import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from configparser import ConfigParser
from sqlalchemy import create_engine
import pandas as pd


# Read config file
config = ConfigParser()
config.read('flask_app.cfg')
database_uri = config.get('SQLAlchemy', 'database_uri')

# Connect to database
db = create_engine(database_uri)

# Get unique device ID's
query = "SELECT DISTINCT device FROM measurements"
res = db.execute(query)
devices = [r['device'] for r in res]

# Dash application
app = dash.Dash('Plant Monitor')
app.layout = html.Div([
    dcc.Dropdown(
        id='dropdown_device',
        options=[{'label': x, 'value': x} for x in devices],
        value=devices[0]
    ),
    dcc.Graph(id='graph_temperature')
], style={'width': '500'})


@app.callback(Output('graph_temperature', 'figure'), [Input('dropdown_device', 'value')])
def update_graph_temperature(device):
    query = "SELECT * FROM measurements WHERE device='{}'".format(device)
    df = pd.read_sql_query(query, con=db)
    print(df)
    return {
        'data': [{
            'x': df['time'],
            'y': df['temperature']
        }],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


if __name__ == '__main__':
    # Specify host 0.0.0.0 to make the service visible to the outside world.
    app.run_server(host='0.0.0.0', port=8050)
