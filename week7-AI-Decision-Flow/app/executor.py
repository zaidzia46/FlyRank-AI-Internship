"""
Walks the graph from start_node, calling `decide(prompt) -> "YES"|"NO"` at
each decision node, until it hits a terminal node or a safety cap.

Deliberately decoupled from Inngest: `run()` here is plain Python that
takes a `decide` callable and a `record_step` callback. The Inngest
function in inngest_client.py wraps each call to `decide` in ctx.step.run
and calls `record_step` after each one - but the traversal logic itself
is unit-testable with a fake decide() and no Inngest runtime at all.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Callable

from app.graph import Graph

MAX_STEPS = 25  # safety cap - the graph may contain a cycle


class WorkflowError(Exception):
    pass


@dataclass
class StepRecord:
    step_number: int
    node_id: str
    node_label: str
    prompt: str | None
    result: str | None  # "YES" / "NO" / None for terminal nodes
    timestamp: str
    error: str | None = None


def run(
    graph: Graph,
    decide: Callable[[str], str],
    record_step: Callable[[StepRecord], None] | None = None,
) -> list[StepRecord]:
    """
    Traverses the graph starting at graph.start_node.
    `decide(prompt) -> "YES"|"NO"` is called once per decision node.
    `record_step`, if given, is called immediately after each step (so a
    caller can stream progress rather than waiting for the whole trace).
    Raises WorkflowError on an invalid graph or too many steps (likely a cycle).
    """
    problems = graph.validate()
    if problems:
        raise WorkflowError("graph is not valid: " + "; ".join(problems))

    trace: list[StepRecord] = []
    current_id = graph.start_node

    for step_number in range(1, MAX_STEPS + 1):
        node = graph.nodes[current_id]

        if node.type == "terminal":
            record = StepRecord(
                step_number=step_number,
                node_id=node.id,
                node_label=node.label,
                prompt=None,
                result=None,
                timestamp=_now(),
            )
            trace.append(record)
            if record_step:
                record_step(record)
            return trace

        # decision node
        try:
            result = decide(node.prompt)
        except Exception as exc:
            record = StepRecord(
                step_number=step_number,
                node_id=node.id,
                node_label=node.label,
                prompt=node.prompt,
                result=None,
                timestamp=_now(),
                error=str(exc),
            )
            trace.append(record)
            if record_step:
                record_step(record)
            raise WorkflowError(f"decision failed at node '{node.id}': {exc}") from exc

        record = StepRecord(
            step_number=step_number,
            node_id=node.id,
            node_label=node.label,
            prompt=node.prompt,
            result=result,
            timestamp=_now(),
        )
        trace.append(record)
        if record_step:
            record_step(record)

        next_id = graph.next_node(node.id, result)
        if next_id is None:
            raise WorkflowError(f"node '{node.id}' has no outgoing '{result}' edge")
        current_id = next_id

    raise WorkflowError(f"exceeded {MAX_STEPS} steps - the graph likely contains a cycle")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def trace_to_dicts(trace: list[StepRecord]) -> list[dict]:
    return [asdict(r) for r in trace]
