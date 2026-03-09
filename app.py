import os
import logging
import fastf1
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output

logging.getLogger("fastf1").setLevel(logging.WARNING)

os.makedirs("cache", exist_ok=True)
fastf1.Cache.enable_cache("cache")

session = fastf1.get_session(2023, "Monaco", "Q")
session.load()

driver_abbrs = []
for num in session.drivers:
    info = session.get_driver(num)
    driver_abbrs.append(info["Abbreviation"])

laps = session.laps
timing = laps[['Driver', 'LapNumber', 'LapTime', 'Compound', 'SpeedST']].copy().dropna()
timing['LapTime'] = timing['LapTime'].dt.total_seconds().round(3)

app = Dash(__name__)

app.layout = html.Div([
    html.H1("F1 Telemetry Dashboard"),

    html.Div([
        html.Label("Driver 1"),
        dcc.Dropdown(id='driver1', options=driver_abbrs, value=driver_abbrs[0])
    ], style={'width': '45%', 'display': 'inline-block'}),

    html.Div([
        html.Label("Driver 2"),
        dcc.Dropdown(id='driver2', options=driver_abbrs, value=driver_abbrs[1])
    ], style={'width': '45%', 'display': 'inline-block'}),

    dcc.Graph(id="speed_graph"),
    dcc.Graph(id="throttle_graph"),
    dcc.Graph(id="track_map"),

    html.H2("Lap Timing Table"),
    dcc.Graph(figure={
        'data': [go.Table(
            header=dict(values=list(timing.columns)),
            cells=dict(values=[timing[col] for col in timing.columns])
        )]
    })
])


@app.callback(
    Output("speed_graph", "figure"),
    Output("throttle_graph", "figure"),
    Output("track_map", "figure"),
    Input("driver1", "value"),
    Input("driver2", "value")
)
def update_graphs(d1, d2):
    lap1 = session.laps.pick_driver(d1).pick_fastest()
    lap2 = session.laps.pick_driver(d2).pick_fastest()

    tel1 = lap1.get_car_data().add_distance()
    tel2 = lap2.get_car_data().add_distance()

    speed_fig = go.Figure()
    speed_fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Speed'], mode='lines', name=d1))
    speed_fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Speed'], mode='lines', name=d2))
    speed_fig.update_layout(title="Speed Comparison")

    throttle_fig = go.Figure()
    throttle_fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Throttle'], mode='lines', name=d1))
    throttle_fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Throttle'], mode='lines', name=d2))
    throttle_fig.update_layout(title="Throttle Comparison")

    pos1 = lap1.get_pos_data()
    pos2 = lap2.get_pos_data()
    track_fig = go.Figure()
    track_fig.add_trace(go.Scatter(x=pos1['X'], y=pos1['Y'], mode='lines', name=d1))
    track_fig.add_trace(go.Scatter(x=pos2['X'], y=pos2['Y'], mode='lines', name=d2))
    track_fig.update_layout(title="Track Map", yaxis=dict(scaleanchor="x"))

    return speed_fig, throttle_fig, track_fig


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)