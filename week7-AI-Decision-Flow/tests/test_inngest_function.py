import os
import sys
import pathlib
import types

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

os.environ["LLM_BASE_URL"] = "http://127.0.0.1:8981/v1"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_MODEL"] = "mock-model"
os.environ["MOCK_PORT"] = "8981"

from tests.mock_llm_server import start_server, call_count
httpd = start_server()

import inngest
from app.inngest_client import run_workflow
from app import store
from app.ui_helpers import example_workflow


class FakeStep:
    def run(self, step_id, handler):
        return handler()


class FakeEvent:
    def __init__(self, data):
        self.data = data


class FakeContext:
    def __init__(self, data):
        self.event = FakeEvent(data)
        self.step = FakeStep()


def set_scenario(name):
    os.environ["MOCK_SCENARIO"] = name
    call_count["n"] = 0


# 1) happy path, YES branch
set_scenario("clean_yes")
graph_dict = example_workflow().to_dict()
run_id = "test-run-1"
store.start_run(run_id, graph_dict)
ctx = FakeContext({"run_id": run_id, "graph": graph_dict})
result = run_workflow._handler(ctx)
run = store.get_run(run_id)
assert run["status"] == "done", run
assert [s["node_id"] for s in run["steps"]] == ["start", "support"], run["steps"]
assert run["steps"][0]["result"] == "YES"
print("PASS: real run_workflow() body executes the YES path end to end, writes to the store")

# 2) NO branch
set_scenario("clean_no")
run_id = "test-run-2"
store.start_run(run_id, graph_dict)
ctx = FakeContext({"run_id": run_id, "graph": graph_dict})
run_workflow._handler(ctx)
run = store.get_run(run_id)
assert [s["node_id"] for s in run["steps"]] == ["start", "sales"], run["steps"]
print("PASS: real run_workflow() body executes the NO path end to end")

# 3) unrepairable model output -> run marked as error, NonRetriableError raised
set_scenario("garbage_always")
run_id = "test-run-3"
store.start_run(run_id, graph_dict)
ctx = FakeContext({"run_id": run_id, "graph": graph_dict})
try:
    run_workflow._handler(ctx)
    assert False, "should have raised"
except inngest.NonRetriableError:
    run = store.get_run(run_id)
    assert run["status"] == "error"
    assert "decision failed" in run["error"]
    print(f"PASS: an unrepairable model answer marks the run as error and raises NonRetriableError: {run['error']}")

# 4) invalid graph is rejected before any model call
set_scenario("clean_yes")
call_count["n"] = 0
bad_graph = {"nodes": {"a": {"id": "a", "label": "A", "type": "decision", "prompt": "a?"}},
             "edges": [], "start_node": "a"}  # decision node with no edges
run_id = "test-run-4"
store.start_run(run_id, bad_graph)
ctx = FakeContext({"run_id": run_id, "graph": bad_graph})
try:
    run_workflow._handler(ctx)
    assert False, "should have raised"
except inngest.NonRetriableError as e:
    assert call_count["n"] == 0, "the model must never be called on an invalid graph"
    run = store.get_run(run_id)
    assert run["status"] == "error"
    print(f"PASS: an invalid graph is rejected before any model call: {e}")

httpd.shutdown()
print("\nALL INNGEST FUNCTION TESTS PASSED")
