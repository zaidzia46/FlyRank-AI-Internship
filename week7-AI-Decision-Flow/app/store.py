"""
A plain in-memory store for run progress, keyed by run_id. Dash's frontend
polls this (via a small Flask endpoint) while the Inngest function writes
to it after every step. Works because Dash and the Inngest handler share
one Flask process - no external database needed for this project's scope.

Not multi-process safe (fine for local dev / a single dev-server instance,
which is what Inngest's dev server assumes anyway).
"""
import threading
from datetime import datetime, timezone

_lock = threading.Lock()
_runs: dict[str, dict] = {}


def start_run(run_id: str, graph_snapshot: dict) -> None:
    with _lock:
        _runs[run_id] = {
            "run_id": run_id,
            "status": "running",  # running | done | error
            "graph_snapshot": graph_snapshot,
            "steps": [],
            "error": None,
            "started_at": _now(),
            "finished_at": None,
        }


def append_step(run_id: str, step: dict) -> None:
    with _lock:
        if run_id in _runs:
            _runs[run_id]["steps"].append(step)


def finish_run(run_id: str, error: str | None = None) -> None:
    with _lock:
        if run_id in _runs:
            _runs[run_id]["status"] = "error" if error else "done"
            _runs[run_id]["error"] = error
            _runs[run_id]["finished_at"] = _now()


def get_run(run_id: str) -> dict | None:
    with _lock:
        run = _runs.get(run_id)
        return dict(run) if run else None


def list_runs() -> list[dict]:
    with _lock:
        return sorted(_runs.values(), key=lambda r: r["started_at"], reverse=True)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
