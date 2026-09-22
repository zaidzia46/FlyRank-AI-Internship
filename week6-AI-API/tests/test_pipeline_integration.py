import os
import sys
import json
import pathlib
import importlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

os.environ["LLM_BASE_URL"] = "http://127.0.0.1:8935/v1"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_MODEL"] = "mock-model"

from tests.mock_llm_server import start_server, call_count

httpd = start_server()


def set_scenario(name):
    os.environ["MOCK_SCENARIO"] = name
    call_count["n"] = 0


def reload_pipeline():
    # fresh import so module-level constants (quarantine path) are picked up cleanly
    if "src.llm.pipeline" in sys.modules:
        importlib.reload(sys.modules["src.llm.pipeline"])
    from src.llm import pipeline
    return pipeline


quarantine_path = pathlib.Path(__file__).parent.parent / "logs" / "quarantine.jsonl"
quarantine_path.unlink(missing_ok=True)

pipeline = reload_pipeline()

# 1) plain valid response
set_scenario("ok")
result = pipeline.run_triage("I was charged twice this month")
assert result.category == "billing"
print("PASS: valid response parses and validates ->", result.model_dump())

# 2) code-fenced response still parses
set_scenario("fence")
result = pipeline.run_triage("test")
assert result.category == "billing"
print("PASS: code-fenced JSON is stripped and parsed")

# 3) malformed once, repaired successfully
set_scenario("malformed_once")
result = pipeline.run_triage("test")
assert result.category == "billing"
assert call_count["n"] == 2, f"expected exactly 2 calls (original + 1 repair), got {call_count['n']}"
print(f"PASS: malformed JSON repaired on 1 retry (calls={call_count['n']})")

# 4) malformed twice -> UnrepairableOutput, quarantined, never crashes
set_scenario("malformed_twice")
try:
    pipeline.run_triage("test")
    assert False, "should have raised UnrepairableOutput"
except pipeline.UnrepairableOutput as e:
    assert call_count["n"] == 2, f"expected 2 calls total, got {call_count['n']}"
    print(f"PASS: unrepairable output raises cleanly (calls={call_count['n']}), reason={e.reason[:40]}...")

quarantine_lines = quarantine_path.read_text().strip().splitlines()
assert len(quarantine_lines) == 1, f"expected 1 quarantine line, got {len(quarantine_lines)}"
entry = json.loads(quarantine_lines[0])
assert entry["prompt_version"] == "triage-v1"
print("PASS: quarantine log has 1 entry with prompt_version and reason")

# 5) valid JSON but category outside the enum -> validation failure -> repair path taken
set_scenario("wrong_enum")
try:
    pipeline.run_triage("test")
    assert False, "should have raised (wrong_enum never becomes valid, no repair scenario configured for it)"
except pipeline.UnrepairableOutput:
    print("PASS: a category outside the closed list is a validation failure, not a silent pass")

# 6) 429 then success -> retried with backoff, eventually succeeds
set_scenario("rate_limit_then_ok")
result = pipeline.run_triage("test")
assert result.category == "billing"
assert call_count["n"] == 2, f"expected 2 calls (1 failed + 1 retry), got {call_count['n']}"
print(f"PASS: 429 is retried and succeeds (calls={call_count['n']})")

# 7) persistent 500 -> retries exhaust -> ModelUnavailable, never crashes
set_scenario("server_error_persistent")
try:
    pipeline.run_triage("test")
    assert False, "should have raised ModelUnavailable"
except pipeline.ModelUnavailable:
    # MAX_RETRIES=2 means up to 3 attempts total
    assert call_count["n"] == pipeline.MAX_RETRIES + 1, f"expected {pipeline.MAX_RETRIES + 1} calls, got {call_count['n']}"
    print(f"PASS: persistent 5xx retries then fails cleanly (calls={call_count['n']})")

# 8) 401 -> never retried, fails immediately
set_scenario("unauthorized")
try:
    pipeline.run_triage("test")
    assert False, "should have raised ModelUnavailable"
except pipeline.ModelUnavailable:
    assert call_count["n"] == 1, f"401 must NOT be retried - expected 1 call, got {call_count['n']}"
    print(f"PASS: 401 is never retried (calls={call_count['n']})")

# 9) timeout -> client timeout shorter than server delay
set_scenario("slow")
pipeline.DEFAULT_TIMEOUT_SECONDS = 0.3  # patch for this test only
try:
    pipeline.run_triage("test")
    assert False, "should have raised ModelTimeout"
except pipeline.ModelTimeout:
    print(f"PASS: slow response triggers ModelTimeout (calls={call_count['n']})")

httpd.shutdown()
print("\nALL PIPELINE INTEGRATION CHECKS PASSED")
