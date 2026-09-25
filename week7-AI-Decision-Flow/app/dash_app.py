"""
The visual flow editor. Pure Python (Dash compiles this to a browser UI -
no JSX/React written by us). Mounted on the same Flask server that serves
the Inngest function (see app/server.py), so one process runs both.
"""
import json
import uuid

import dash
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context, no_update

from app.graph import Graph, Node, Edge
from app.ui_helpers import graph_to_cytoscape_elements, STYLESHEET, example_workflow
from app import store
from app.inngest_client import client as inngest_client
import inngest


def create_dash_app(server) -> dash.Dash:
    dash_app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="AI Workflow Visualizer",
    )

    dash_app.layout = _layout()
    _register_callbacks(dash_app)
    return dash_app


def _layout():
    initial_graph = example_workflow().to_dict()

    sidebar = dbc.Card([
        dbc.CardHeader("Build the workflow"),
        dbc.CardBody([
            html.H6("Add node"),
            dbc.Input(id="node-id-input", placeholder="node id (e.g. check_urgency)", className="mb-1"),
            dbc.Input(id="node-label-input", placeholder="short label shown on canvas", className="mb-1"),
            dcc.Dropdown(
                id="node-type-input",
                options=[{"label": "Decision (asks the model YES/NO)", "value": "decision"},
                         {"label": "Terminal (end of a path)", "value": "terminal"}],
                value="decision", className="mb-1",
            ),
            dbc.Textarea(id="node-prompt-input", placeholder="Prompt (decision nodes only) - a yes/no question",
                         className="mb-1", style={"height": "70px"}),
            dbc.Button("Add / update node", id="add-node-btn", color="primary", size="sm", className="mb-3 w-100"),

            html.H6("Connect nodes"),
            dcc.Dropdown(id="edge-source-input", placeholder="from (decision node)", className="mb-1"),
            dcc.Dropdown(id="edge-target-input", placeholder="to", className="mb-1"),
            dcc.Dropdown(id="edge-condition-input",
                         options=[{"label": "YES", "value": "YES"}, {"label": "NO", "value": "NO"}],
                         placeholder="condition", className="mb-1"),
            dbc.Button("Add / update edge", id="add-edge-btn", color="primary", size="sm", className="mb-3 w-100"),

            html.H6("Start node"),
            dcc.Dropdown(id="start-node-input", placeholder="which node runs first", className="mb-3"),

            dbc.Button("Load example (Support/Sales)", id="load-example-btn", color="secondary", size="sm",
                       outline=True, className="mb-1 w-100"),
            dbc.Button("Clear graph", id="clear-graph-btn", color="danger", size="sm", outline=True,
                       className="mb-3 w-100"),

            html.Hr(),
            dbc.Row([
                dbc.Col(dbc.Button("Export JSON", id="export-btn", color="secondary", size="sm", className="w-100")),
                dbc.Col(dcc.Upload(
                    dbc.Button("Import JSON", color="secondary", size="sm", className="w-100"),
                    id="import-upload",
                )),
            ], className="mb-3"),
            dcc.Download(id="download-json"),

            dbc.Button("Run workflow", id="run-btn", color="success", className="w-100 mb-2"),
            html.Div(id="validation-messages"),
        ]),
    ], style={"width": "340px", "overflowY": "auto"})

    canvas = dbc.Card([
        dbc.CardHeader("Workflow canvas"),
        dbc.CardBody([
            cyto.Cytoscape(
                id="cytoscape-graph",
                layout={"name": "breadthfirst", "directed": True, "padding": 20},
                style={"width": "100%", "height": "480px"},
                stylesheet=STYLESHEET,
                elements=graph_to_cytoscape_elements(Graph.from_dict(initial_graph)),
            ),
        ]),
    ], style={"flex": 1})

    log_panel = dbc.Card([
        dbc.CardHeader(id="log-header", children="Execution log"),
        dbc.CardBody(id="log-panel", children=[html.Small("Run the workflow to see step-by-step results here.",
                                                            className="text-muted")],
                     style={"maxHeight": "220px", "overflowY": "auto"}),
    ], className="mt-2")

    return html.Div([
        dcc.Store(id="graph-store", data=initial_graph),
        dcc.Store(id="run-id-store", data=None),
        dcc.Interval(id="poll-interval", interval=700, disabled=True),

        dbc.Container([
            html.H3("AI Workflow Visualizer", className="my-3"),
            html.P("Each decision node asks a model a yes/no question and branches on the answer. "
                   "Execution runs through Inngest; this canvas visualizes it.", className="text-muted"),
            dbc.Row([
                dbc.Col(sidebar, width="auto"),
                dbc.Col([canvas, log_panel]),
            ], className="g-3"),
        ], fluid=True),
    ])


def _register_callbacks(app: dash.Dash):

    # ---- keep dropdowns in sync with the current graph ----
    @app.callback(
        Output("edge-source-input", "options"),
        Output("edge-target-input", "options"),
        Output("start-node-input", "options"),
        Input("graph-store", "data"),
    )
    def refresh_dropdowns(graph_data):
        graph = Graph.from_dict(graph_data)
        options = [{"label": f"{n.id} ({n.type})", "value": n.id} for n in graph.nodes.values()]
        decision_options = [o for o in options if "(decision)" in o["label"]]
        return decision_options, options, options

    # ---- add / update a node ----
    @app.callback(
        Output("graph-store", "data", allow_duplicate=True),
        Input("add-node-btn", "n_clicks"),
        State("node-id-input", "value"),
        State("node-label-input", "value"),
        State("node-type-input", "value"),
        State("node-prompt-input", "value"),
        State("graph-store", "data"),
        prevent_initial_call=True,
    )
    def add_node(n_clicks, node_id, label, node_type, prompt, graph_data):
        if not node_id or not node_id.strip():
            return no_update
        graph = Graph.from_dict(graph_data)
        graph.add_node(Node(
            id=node_id.strip(),
            label=(label or node_id).strip(),
            type=node_type or "decision",
            prompt=(prompt or "").strip() or None if node_type == "decision" else None,
        ))
        return graph.to_dict()

    # ---- add / update an edge ----
    @app.callback(
        Output("graph-store", "data", allow_duplicate=True),
        Output("validation-messages", "children"),
        Input("add-edge-btn", "n_clicks"),
        State("edge-source-input", "value"),
        State("edge-target-input", "value"),
        State("edge-condition-input", "value"),
        State("graph-store", "data"),
        prevent_initial_call=True,
    )
    def add_edge(n_clicks, source, target, condition, graph_data):
        if not (source and target and condition):
            return no_update, dbc.Alert("Pick a source, target, and condition first.", color="warning", dismissable=True)
        graph = Graph.from_dict(graph_data)
        try:
            graph.add_edge(Edge(source=source, target=target, condition=condition))
        except ValueError as exc:
            return no_update, dbc.Alert(str(exc), color="danger", dismissable=True)
        return graph.to_dict(), ""

    # ---- set start node ----
    @app.callback(
        Output("graph-store", "data", allow_duplicate=True),
        Input("start-node-input", "value"),
        State("graph-store", "data"),
        prevent_initial_call=True,
    )
    def set_start_node(node_id, graph_data):
        if not node_id:
            return no_update
        graph = Graph.from_dict(graph_data)
        graph.start_node = node_id
        return graph.to_dict()

    # ---- load example / clear ----
    @app.callback(
        Output("graph-store", "data", allow_duplicate=True),
        Input("load-example-btn", "n_clicks"),
        Input("clear-graph-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def load_or_clear(load_clicks, clear_clicks):
        triggered = callback_context.triggered_id
        if triggered == "load-example-btn":
            return example_workflow().to_dict()
        return Graph().to_dict()

    # ---- export ----
    @app.callback(
        Output("download-json", "data"),
        Input("export-btn", "n_clicks"),
        State("graph-store", "data"),
        prevent_initial_call=True,
    )
    def export_json(n_clicks, graph_data):
        return dict(content=json.dumps(graph_data, indent=2), filename="workflow.json")

    # ---- import ----
    @app.callback(
        Output("graph-store", "data", allow_duplicate=True),
        Input("import-upload", "contents"),
        prevent_initial_call=True,
    )
    def import_json(contents):
        if not contents:
            return no_update
        import base64
        _, b64data = contents.split(",", 1)
        data = json.loads(base64.b64decode(b64data))
        graph = Graph.from_dict(data)  # round-trips through the same validated model
        return graph.to_dict()

    # ---- render the canvas whenever the graph or the run status changes ----
    @app.callback(
        Output("cytoscape-graph", "elements"),
        Input("graph-store", "data"),
        Input("run-id-store", "data"),
        Input("poll-interval", "n_intervals"),
    )
    def render_canvas(graph_data, run_id, _n):
        graph = Graph.from_dict(graph_data)
        run = store.get_run(run_id) if run_id else None
        return graph_to_cytoscape_elements(graph, run)

    # ---- run the workflow ----
    @app.callback(
        Output("run-id-store", "data"),
        Output("poll-interval", "disabled"),
        Output("validation-messages", "children", allow_duplicate=True),
        Input("run-btn", "n_clicks"),
        State("graph-store", "data"),
        prevent_initial_call=True,
    )
    def run_workflow_click(n_clicks, graph_data):
        graph = Graph.from_dict(graph_data)
        problems = graph.validate()
        if problems:
            return no_update, True, dbc.Alert("Can't run: " + "; ".join(problems), color="danger", dismissable=True)

        run_id = str(uuid.uuid4())
        store.start_run(run_id, graph_snapshot=graph_data)
        inngest_client.send_sync(inngest.Event(name="workflow/run", data={"run_id": run_id, "graph": graph_data}))
        return run_id, False, ""

    # ---- execution log panel + stop polling once finished ----
    @app.callback(
        Output("log-panel", "children"),
        Output("log-header", "children"),
        Output("poll-interval", "disabled", allow_duplicate=True),
        Input("run-id-store", "data"),
        Input("poll-interval", "n_intervals"),
        prevent_initial_call=True,
    )
    def render_log(run_id, _n):
        if not run_id:
            return no_update, no_update, no_update
        run = store.get_run(run_id)
        if not run:
            return [html.Small("Waiting for the workflow to start...", className="text-muted")], "Execution log", False

        rows = []
        for step in run["steps"]:
            if step.get("error"):
                badge = dbc.Badge("ERROR", color="danger", className="me-2")
            elif step.get("result"):
                badge = dbc.Badge(step["result"], color="success" if step["result"] == "YES" else "danger",
                                  className="me-2")
            else:
                badge = dbc.Badge("terminal", color="secondary", className="me-2")
            rows.append(html.Div([
                html.Small(f"#{step['step_number']} "), badge,
                html.Span(step["node_label"], className="fw-bold"),
                html.Br(),
                html.Small(step.get("prompt") or step.get("error") or "(end of path)", className="text-muted"),
            ], className="mb-2 pb-2 border-bottom"))

        header = f"Execution log — {run['status']}"
        still_running = run["status"] == "running"
        return rows, header, not still_running

    # ---- keep the polling interval's own on/off in sync too ----
    @app.callback(
        Output("poll-interval", "disabled", allow_duplicate=True),
        Input("log-panel", "children"),
        State("run-id-store", "data"),
        prevent_initial_call=True,
    )
    def sync_interval(_children, run_id):
        if not run_id:
            return True
        run = store.get_run(run_id)
        return not run or run["status"] != "running"
