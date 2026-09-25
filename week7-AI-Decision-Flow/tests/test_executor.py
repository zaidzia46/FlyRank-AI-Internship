import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from app.graph import Graph, Node, Edge
from app.executor import run, WorkflowError


def support_sales_graph() -> Graph:
    g = Graph()
    g.add_node(Node(id="start", label="Is this a support request?", type="decision", prompt="Is this a support request?"))
    g.add_node(Node(id="support", label="Support", type="terminal"))
    g.add_node(Node(id="sales", label="Sales", type="terminal"))
    g.add_edge(Edge(source="start", target="support", condition="YES"))
    g.add_edge(Edge(source="start", target="sales", condition="NO"))
    g.start_node = "start"
    return g


def test_spec_example_yes_path():
    g = support_sales_graph()
    trace = run(g, decide=lambda prompt: "YES")
    assert [t.node_id for t in trace] == ["start", "support"]
    assert trace[0].result == "YES"
    assert trace[1].result is None  # terminal node
    print("PASS: YES path reaches Support terminal node, exactly as in the spec example")


def test_spec_example_no_path():
    g = support_sales_graph()
    trace = run(g, decide=lambda prompt: "NO")
    assert [t.node_id for t in trace] == ["start", "sales"]
    print("PASS: NO path reaches Sales terminal node")


def test_multi_hop_chain():
    g = Graph()
    g.add_node(Node(id="a", label="A", type="decision", prompt="a?"))
    g.add_node(Node(id="b", label="B", type="decision", prompt="b?"))
    g.add_node(Node(id="c", label="C", type="decision", prompt="c?"))
    g.add_node(Node(id="end", label="End", type="terminal"))
    g.add_node(Node(id="dead_end", label="Dead end", type="terminal"))
    g.add_edge(Edge(source="a", target="b", condition="YES"))
    g.add_edge(Edge(source="a", target="dead_end", condition="NO"))
    g.add_edge(Edge(source="b", target="c", condition="YES"))
    g.add_edge(Edge(source="b", target="dead_end", condition="NO"))
    g.add_edge(Edge(source="c", target="end", condition="YES"))
    g.add_edge(Edge(source="c", target="dead_end", condition="NO"))
    g.start_node = "a"

    trace = run(g, decide=lambda prompt: "YES")
    assert [t.node_id for t in trace] == ["a", "b", "c", "end"]
    print("PASS: multi-hop chain (a -> b -> c -> end) traverses in order")


def test_invalid_graph_raises_before_calling_model():
    g = Graph()
    g.add_node(Node(id="a", label="A", type="decision", prompt="a?"))  # no edges, no terminal
    g.start_node = "a"
    calls = []
    try:
        run(g, decide=lambda p: calls.append(p) or "YES")
        assert False, "should have raised WorkflowError"
    except WorkflowError as e:
        assert calls == [], "the model should never be called on an invalid graph"
        print(f"PASS: invalid graph rejected before any model call: {e}")


def test_decide_exception_is_recorded_and_raised():
    g = support_sales_graph()

    def flaky_decide(prompt):
        raise RuntimeError("model unavailable")

    try:
        run(g, decide=flaky_decide)
        assert False, "should have raised WorkflowError"
    except WorkflowError as e:
        assert "model unavailable" in str(e)
        print(f"PASS: a decide() failure surfaces as WorkflowError: {e}")


def test_cycle_is_caught_by_max_steps():
    g = Graph()
    g.add_node(Node(id="a", label="A", type="decision", prompt="a?"))
    g.add_node(Node(id="b", label="B", type="decision", prompt="b?"))
    g.add_node(Node(id="dead_end", label="Dead end", type="terminal"))
    # a and b point at each other on YES - a genuine cycle
    g.add_edge(Edge(source="a", target="b", condition="YES"))
    g.add_edge(Edge(source="a", target="dead_end", condition="NO"))
    g.add_edge(Edge(source="b", target="a", condition="YES"))
    g.add_edge(Edge(source="b", target="dead_end", condition="NO"))
    g.start_node = "a"

    try:
        run(g, decide=lambda prompt: "YES")  # always YES -> infinite a<->b loop
        assert False, "should have raised WorkflowError"
    except WorkflowError as e:
        assert "cycle" in str(e) or "steps" in str(e)
        print(f"PASS: a cycle is caught by the step cap, not an infinite loop: {e}")


def test_record_step_streams_progress():
    g = support_sales_graph()
    streamed = []
    run(g, decide=lambda prompt: "YES", record_step=streamed.append)
    assert len(streamed) == 2
    assert streamed[0].node_id == "start"
    print("PASS: record_step is called incrementally as each node completes")


if __name__ == "__main__":
    test_spec_example_yes_path()
    test_spec_example_no_path()
    test_multi_hop_chain()
    test_invalid_graph_raises_before_calling_model()
    test_decide_exception_is_recorded_and_raised()
    test_cycle_is_caught_by_max_steps()
    test_record_step_streams_progress()
    print("\nALL EXECUTOR TESTS PASSED")
