import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from app.graph import Graph, Node, Edge


def test_build_support_sales_example():
    g = Graph()
    g.add_node(Node(id="start", label="Is this a support request?", type="decision", prompt="Is this a support request?"))
    g.add_node(Node(id="support", label="Support", type="terminal"))
    g.add_node(Node(id="sales", label="Sales", type="terminal"))
    g.add_edge(Edge(source="start", target="support", condition="YES"))
    g.add_edge(Edge(source="start", target="sales", condition="NO"))
    g.start_node = "start"

    assert g.validate() == []
    assert g.next_node("start", "YES") == "support"
    assert g.next_node("start", "NO") == "sales"
    print("PASS: build + validate the worked example from the spec")


def test_decision_node_missing_edge_fails_validation():
    g = Graph()
    g.add_node(Node(id="start", label="q", type="decision", prompt="q?"))
    g.add_node(Node(id="a", label="A", type="terminal"))
    g.add_edge(Edge(source="start", target="a", condition="YES"))
    g.start_node = "start"
    # no NO edge added
    problems = g.validate()
    assert any("NO edge" in p for p in problems)
    print("PASS: missing NO edge is caught by validate()")


def test_terminal_node_cannot_have_outgoing_edges():
    g = Graph()
    g.add_node(Node(id="a", label="A", type="terminal"))
    g.add_node(Node(id="b", label="B", type="terminal"))
    try:
        g.add_edge(Edge(source="a", target="b", condition="YES"))
        assert False, "should have raised - 'a' is not a decision node"
    except ValueError:
        print("PASS: terminal node can't be an edge source")


def test_re_adding_edge_of_same_condition_replaces_it():
    g = Graph()
    g.add_node(Node(id="start", label="q", type="decision", prompt="q?"))
    g.add_node(Node(id="a", label="A", type="terminal"))
    g.add_node(Node(id="b", label="B", type="terminal"))
    g.add_edge(Edge(source="start", target="a", condition="YES"))
    g.add_edge(Edge(source="start", target="b", condition="YES"))  # replaces the first
    out = g.outgoing("start")
    assert out["YES"] == "b"
    assert len([e for e in g.edges if e.source == "start" and e.condition == "YES"]) == 1
    print("PASS: re-adding a YES edge replaces the old one, not duplicates it")


def test_remove_node_cleans_up_edges_and_start():
    g = Graph()
    g.add_node(Node(id="start", label="q", type="decision", prompt="q?"))
    g.add_node(Node(id="a", label="A", type="terminal"))
    g.add_edge(Edge(source="start", target="a", condition="YES"))
    g.start_node = "start"
    g.remove_node("start")
    assert "start" not in g.nodes
    assert g.edges == []
    assert g.start_node is None
    print("PASS: removing a node cleans up its edges and clears start_node if needed")


def test_round_trip_serialization():
    g = Graph()
    g.add_node(Node(id="start", label="q", type="decision", prompt="q?"))
    g.add_node(Node(id="a", label="A", type="terminal"))
    g.add_edge(Edge(source="start", target="a", condition="YES"))
    g.add_edge(Edge(source="start", target="a", condition="NO"))
    g.start_node = "start"

    data = g.to_dict()
    g2 = Graph.from_dict(data)
    assert g2.to_dict() == data
    assert g2.validate() == []
    print("PASS: to_dict/from_dict round-trips exactly")


if __name__ == "__main__":
    test_build_support_sales_example()
    test_decision_node_missing_edge_fails_validation()
    test_terminal_node_cannot_have_outgoing_edges()
    test_re_adding_edge_of_same_condition_replaces_it()
    test_remove_node_cleans_up_edges_and_start()
    test_round_trip_serialization()
    print("\nALL GRAPH TESTS PASSED")
