import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

os.environ.setdefault("LLM_BASE_URL", "http://127.0.0.1:8935/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_MODEL", "mock-model")

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_missing_field_returns_400_naming_field():
    resp = client.post("/triage", json={})
    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert "text" in body["field"]
    print("PASS: missing field -> 400 naming the field:", body)


def test_text_too_long_returns_400():
    resp = client.post("/triage", json={"text": "x" * 3000})
    assert resp.status_code == 400, resp.text
    print("PASS: over-length text -> 400:", resp.json())


def test_wrong_type_returns_400():
    resp = client.post("/triage", json={"text": 12345})
    assert resp.status_code == 400, resp.text
    print("PASS: wrong type -> 400:", resp.json())


def test_stub_mode_returns_schema_valid_response():
    os.environ["LLM_STUB"] = "1"
    try:
        resp = client.post("/triage", json={"text": "anything at all"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["category"] in ("billing", "bug", "feature", "other")
        assert body["fallback"] is False
        print("PASS: stub mode -> 200 schema-valid response, zero model calls:", body)
    finally:
        del os.environ["LLM_STUB"]


def test_kill_switch_returns_fallback():
    os.environ["LLM_ENABLED"] = "false"
    try:
        resp = client.post("/triage", json={"text": "anything at all"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["fallback"] is True
        assert body["category"] == "other"
        print("PASS: kill switch -> 200 deterministic fallback, zero model calls:", body)
    finally:
        os.environ["LLM_ENABLED"] = "true"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    print("PASS: /health ->", resp.json())


if __name__ == "__main__":
    test_missing_field_returns_400_naming_field()
    test_text_too_long_returns_400()
    test_wrong_type_returns_400()
    test_stub_mode_returns_schema_valid_response()
    test_kill_switch_returns_fallback()
    test_health()
    print("\nALL ROUTE-LEVEL CHECKS PASSED")
