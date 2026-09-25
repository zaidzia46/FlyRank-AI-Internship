import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

os.environ["LLM_BASE_URL"] = "http://127.0.0.1:8980/v1"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_MODEL"] = "mock-model"

from tests.mock_llm_server import start_server, call_count
from app.llm import ask_yes_no, DecisionError

httpd = start_server()


def set_scenario(name):
    os.environ["MOCK_SCENARIO"] = name
    call_count["n"] = 0


set_scenario("clean_yes")
assert ask_yes_no("Is this a support request?") == "YES"
print("PASS: clean YES parses directly, 1 call")

set_scenario("clean_no")
assert ask_yes_no("Is this urgent?") == "NO"
print("PASS: clean NO parses directly, 1 call")

set_scenario("messy_yes")
assert ask_yes_no("test") == "YES"
assert call_count["n"] == 1, "should extract YES from prose without needing a repair call"
print("PASS: YES/NO extracted from a sentence, no repair needed")

set_scenario("messy_then_clean")
assert ask_yes_no("test") == "NO"
assert call_count["n"] == 2, f"expected exactly 2 calls (original + repair), got {call_count['n']}"
print("PASS: unparseable first answer repaired successfully on 1 retry")

set_scenario("garbage_always")
try:
    ask_yes_no("test")
    assert False, "should have raised DecisionError"
except DecisionError as e:
    assert call_count["n"] == 2, f"expected exactly 2 calls total, got {call_count['n']}"
    print(f"PASS: unrepairable garbage raises DecisionError cleanly (calls={call_count['n']})")

httpd.shutdown()
print("\nALL LLM TESTS PASSED")
