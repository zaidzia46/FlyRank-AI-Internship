import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from app.ui_helpers import graph_to_cytoscape_elements, example_workflow


def test_no_run_yet_marks_only_start_node():
    g = example_workflow()
    elements = graph_to_cytoscape_elements(g, run=None)
    node_elements = [e for e in elements if "source" not in e["data"]]
    edge_elements = [e for e in elements if "source" in e["data"]]

    assert len(node_elements) == 3
    assert len(edge_elements) == 2
    start = next(e for e in node_elements if e["data"]["id"] == "start")
    assert start["data"]["state"] == "start_marker"
    support = next(e for e in node_elements if e["data"]["id"] == "support")
    assert support["data"]["state"] == ""
    print("PASS: with no run, only the start node is marked; nodes/edges all present")


def test_edge_conditions_carried_through():
    g = example_workflow()
    elements = graph_to_cytoscape_elements(g, run=None)
    edges = {e["data"]["id"]: e["data"] for e in elements if "source" in e["data"]}
    yes_edge = next(d for d in edges.values() if d["source"] == "start" and d["target"] == "support")
    no_edge = next(d for d in edges.values() if d["source"] == "start" and d["target"] == "sales")
    assert yes_edge["condition"] == "YES"
    assert no_edge["condition"] == "NO"
    print("PASS: YES/NO conditions are attached to the right edges for stylesheet selectors")


def test_completed_yes_run_colors_nodes_and_marks_active_edge():
    g = example_workflow()
    run = {
        "status": "done",
        "steps": [
            {"node_id": "start", "result": "YES"},
            {"node_id": "support", "result": None},
        ],
    }
    elements = graph_to_cytoscape_elements(g, run=run)
    nodes = {e["data"]["id"]: e["data"] for e in elements if "source" not in e["data"]}
    edges = {e["data"]["id"]: e["data"] for e in elements if "source" in e["data"]}

    assert nodes["start"]["state"] == "done_yes"
    assert nodes["support"]["state"] == "done_yes"  # reached terminal
    assert nodes["sales"]["state"] == ""  # never visited

    active_edge = next(d for d in edges.values() if d["source"] == "start" and d["target"] == "support")
    inactive_edge = next(d for d in edges.values() if d["source"] == "start" and d["target"] == "sales")
    assert active_edge["active"] == "true"
    assert inactive_edge["active"] == "false"
    print("PASS: completed run colors visited nodes and marks the traversed edge active")


def test_running_state_highlights_last_step():
    g = example_workflow()
    run = {"status": "running", "steps": [{"node_id": "start", "result": None}]}
    elements = graph_to_cytoscape_elements(g, run=run)
    nodes = {e["data"]["id"]: e["data"] for e in elements if "source" not in e["data"]}
    assert nodes["start"]["state"] == "running"
    print("PASS: the node currently being evaluated is marked 'running'")


def test_error_step_marks_error_state():
    g = example_workflow()
    run = {"status": "error", "error": "boom", "steps": [{"node_id": "start", "result": None, "error": "boom"}]}
    elements = graph_to_cytoscape_elements(g, run=run)
    nodes = {e["data"]["id"]: e["data"] for e in elements if "source" not in e["data"]}
    assert nodes["start"]["state"] == "error"
    print("PASS: a failed step marks its node with the error state")


def test_example_workflow_is_itself_valid():
    g = example_workflow()
    assert g.validate() == []
    print("PASS: example_workflow() builds a graph that passes validate()")


if __name__ == "__main__":
    test_no_run_yet_marks_only_start_node()
    test_edge_conditions_carried_through()
    test_completed_yes_run_colors_nodes_and_marks_active_edge()
    test_running_state_highlights_last_step()
    test_error_step_marks_error_state()
    test_example_workflow_is_itself_valid()
    print("\nALL UI HELPER TESTS PASSED")
