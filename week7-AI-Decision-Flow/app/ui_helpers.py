"""
Turns a Graph (+ optional run status) into Cytoscape elements and a
stylesheet. Kept as plain functions, separate from the Dash callbacks
that call them, so this can be unit-tested without a browser.
"""
from app.graph import Graph, Node, Edge

STYLESHEET = [
    {"selector": "node", "style": {
        "label": "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "background-color": "#94a3b8",
        "color": "#0f172a",
        "font-size": "11px",
        "width": "90px",
        "height": "50px",
        "shape": "round-rectangle",
        "border-width": "2px",
        "border-color": "#64748b",
        "text-wrap": "wrap",
        "text-max-width": "80px",
    }},
    {"selector": "node[node_type = 'decision']", "style": {
        "background-color": "#dbeafe", "border-color": "#3b82f6",
    }},
    {"selector": "node[node_type = 'terminal']", "style": {
        "background-color": "#f1f5f9", "border-color": "#64748b", "shape": "ellipse",
    }},
    {"selector": "node[state = 'start_marker']", "style": {
        "border-width": "3px", "border-color": "#a855f7",
    }},
    {"selector": "node[state = 'running']", "style": {
        "border-color": "#f59e0b", "border-width": "4px", "background-color": "#fef3c7",
    }},
    {"selector": "node[state = 'done_yes']", "style": {
        "border-color": "#16a34a", "border-width": "4px", "background-color": "#dcfce7",
    }},
    {"selector": "node[state = 'done_no']", "style": {
        "border-color": "#dc2626", "border-width": "4px", "background-color": "#fee2e2",
    }},
    {"selector": "node[state = 'error']", "style": {
        "border-color": "#dc2626", "border-width": "4px", "background-color": "#450a0a", "color": "#ffffff",
    }},
    {"selector": "edge", "style": {
        "curve-style": "bezier",
        "target-arrow-shape": "triangle",
        "width": 2,
        "label": "data(condition)",
        "font-size": "10px",
    }},
    {"selector": "edge[condition = 'YES']", "style": {
        "line-color": "#16a34a", "target-arrow-color": "#16a34a",
    }},
    {"selector": "edge[condition = 'NO']", "style": {
        "line-color": "#dc2626", "target-arrow-color": "#dc2626", "line-style": "dashed",
    }},
    {"selector": "edge[active = 'true']", "style": {
        "width": 4,
    }},
]


def graph_to_cytoscape_elements(graph: Graph, run: dict | None = None) -> list[dict]:
    """
    run (optional): the dict from app.store.get_run(run_id) - used to color
    nodes by execution state (running / done_yes / done_no / error) and to
    mark which edges were actually traversed.
    """
    steps = run["steps"] if run else []
    steps_by_node = {s["node_id"]: s for s in steps}
    last_step_node = steps[-1]["node_id"] if steps else None
    run_status = run["status"] if run else None

    elements = []
    for node in graph.nodes.values():
        state = None
        if node.id == graph.start_node:
            state = "start_marker"
        step = steps_by_node.get(node.id)
        if step:
            if step.get("error"):
                state = "error"
            elif step.get("result") == "YES":
                state = "done_yes"
            elif step.get("result") == "NO":
                state = "done_no"
            elif node.type == "terminal":
                state = "done_yes"  # reached terminal - highlight it as completed
        if node.id == last_step_node and run_status == "running":
            state = "running"

        elements.append({
            "data": {
                "id": node.id,
                "label": node.label,
                "node_type": node.type,
                "state": state or "",
            }
        })

    traversed_node_ids = {s["node_id"] for s in steps}
    for edge in graph.edges:
        was_traversed = (
            edge.source in traversed_node_ids
            and steps_by_node.get(edge.source, {}).get("result") == edge.condition
        )
        elements.append({
            "data": {
                "id": f"{edge.source}->{edge.target}:{edge.condition}",
                "source": edge.source,
                "target": edge.target,
                "condition": edge.condition,
                "active": "true" if was_traversed else "false",
            }
        })
    return elements


def example_workflow() -> Graph:
    """The exact worked example from the assignment spec."""
    g = Graph()
    g.add_node(Node(id="start", label="Support or\nSales?", type="decision", prompt="Is this a support request?"))
    g.add_node(Node(id="support", label="Support", type="terminal"))
    g.add_node(Node(id="sales", label="Sales", type="terminal"))
    g.add_edge(Edge(source="start", target="support", condition="YES"))
    g.add_edge(Edge(source="start", target="sales", condition="NO"))
    g.start_node = "start"
    return g
