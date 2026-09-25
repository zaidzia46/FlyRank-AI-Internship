"""
The Inngest side: one client, one function. Each node visit becomes its
own Inngest step (ctx.step.run), so Inngest's dev server shows the
step-by-step execution, retries a failed step independently, and memoizes
completed steps if the function is replayed.

Triggered by a "workflow/run" event carrying the graph and a run_id (the
run_id is ours, not Inngest's internal one - generated client-side so the
frontend can start polling for progress before the function has even
picked up the event).
"""
import os
import inngest

from app.graph import Graph
from app.llm import ask_yes_no, DecisionError
from app import store

client = inngest.Inngest(
    app_id="ai-workflow-visualizer",
    is_production=False,
    event_api_base_url=os.environ.get("INNGEST_EVENT_API_BASE_URL"),
    api_base_url=os.environ.get("INNGEST_API_BASE_URL"),
)


@client.create_function(
    fn_id="run-workflow",
    trigger=inngest.TriggerEvent(event="workflow/run"),
    retries=0,  # our own repair-retry lives inside ask_yes_no(); a whole-step retry would re-ask a settled decision
)
def run_workflow(ctx: inngest.ContextSync) -> dict:
    run_id = ctx.event.data["run_id"]
    graph = Graph.from_dict(ctx.event.data["graph"])

    problems = graph.validate()
    if problems:
        error = "graph is not valid: " + "; ".join(problems)
        store.finish_run(run_id, error=error)
        raise inngest.NonRetriableError(error)

    current_id = graph.start_node
    MAX_STEPS = 25

    for step_number in range(1, MAX_STEPS + 1):
        node = graph.nodes[current_id]

        if node.type == "terminal":
            store.append_step(run_id, {
                "step_number": step_number,
                "node_id": node.id,
                "node_label": node.label,
                "prompt": None,
                "result": None,
            })
            store.finish_run(run_id)
            return {"run_id": run_id, "status": "done", "final_node": node.id}

        # each decision becomes its own durable Inngest step
        def make_step(node_id: str, prompt: str):
            def step_fn():
                return ask_yes_no(prompt)
            return step_fn

        try:
            result = ctx.step.run(f"node-{node.id}", make_step(node.id, node.prompt))
        except DecisionError as exc:
            store.append_step(run_id, {
                "step_number": step_number,
                "node_id": node.id,
                "node_label": node.label,
                "prompt": node.prompt,
                "result": None,
                "error": str(exc),
            })
            store.finish_run(run_id, error=f"decision failed at node '{node.id}': {exc}")
            raise inngest.NonRetriableError(str(exc)) from exc

        store.append_step(run_id, {
            "step_number": step_number,
            "node_id": node.id,
            "node_label": node.label,
            "prompt": node.prompt,
            "result": result,
        })

        next_id = graph.next_node(node.id, result)
        if next_id is None:
            error = f"node '{node.id}' has no outgoing '{result}' edge"
            store.finish_run(run_id, error=error)
            raise inngest.NonRetriableError(error)
        current_id = next_id

    error = f"exceeded {MAX_STEPS} steps - the graph likely contains a cycle"
    store.finish_run(run_id, error=error)
    raise inngest.NonRetriableError(error)
