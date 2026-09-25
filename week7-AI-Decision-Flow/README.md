# AI Workflow Visualizer

A visual workflow builder where each node is an AI decision step that answers exactly `YES`
or `NO`, branching to the next node accordingly. Execution runs through **Inngest**; the
canvas is drawn with **Dash + dash-cytoscape**.

## A note on the tech stack

The original spec calls for React Flow, Shadcn, and Inngest, with a React/Next.js frontend.
**This build is pure Python, no React/JSX anywhere**, per request. The substitutions:

| Spec asked for | Used instead | Why it's a fair substitute |
|---|---|---|
| React Flow | **Dash + dash-cytoscape** | Real node/edge graph rendering, written entirely in Python - Dash compiles the UI, you never touch JSX |
| Shadcn | **Dash Bootstrap Components** | Pure-Python styled forms, buttons, cards |
| Inngest | **Inngest's official Python SDK** | The same Inngest, genuinely - not a workaround. Each node visit is a real `ctx.step.run()` |
| OpenAI SDK | **openai** (Python) | As specified |

Dash and the Inngest function handler are mounted on **one Flask server** (`app/server.py`),
so this is a single Python process - no separate frontend/backend repos.

## Project structure

```
app/
  graph.py           - the workflow data model (nodes, edges, validation)
  executor.py         - pure graph-traversal logic (decoupled from Inngest, unit-testable)
  llm.py               - strict YES/NO model caller, with one repair retry
  ui_helpers.py       - graph -> Cytoscape elements + stylesheet (YES/NO edge styling, execution-state coloring)
  inngest_client.py  - the Inngest client + the run-workflow function (one ctx.step.run per node)
  store.py             - in-process run-status store, polled by the frontend
  dash_app.py         - the visual editor: layout + all callbacks
  server.py            - Flask app serving Dash (at /) and Inngest (at /api/inngest)
tests/                - unit + integration tests (see "Verification" below)
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in a real LLM_API_KEY
```

Two provider lanes work unmodified (same pattern as the rest of this program) - just change
three env vars in `.env`:

| | OpenRouter (hosted, free tier) | Ollama (local) |
|---|---|---|
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | `http://localhost:11434/v1/` |
| `LLM_API_KEY` | your real key | the literal string `ollama` |
| `LLM_MODEL` | `openrouter/free` | `gemma3:1b` |

## Run it

**Terminal 1 — the app (Dash UI + Inngest handler, one process):**
```bash
python -m app.server
```
Now open **http://localhost:8000**.

**Terminal 2 — Inngest's dev server** (this is standard for any Inngest project, regardless
of language - it needs Node.js/npx, but runs no application code, just the Inngest dashboard
and step orchestrator):
```bash
npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
```
Open **http://localhost:8288** to watch each node's step execute in Inngest's own dashboard.

## Using it

1. Click **"Load example (Support/Sales)"** to load the exact worked example from the spec:
   a `start` decision node ("Is this a support request?") branching YES → Support, NO → Sales.
2. Or build your own: add a node (give it an id, a label, a type, and - for decision nodes -
   a yes/no prompt), then connect nodes with YES/NO edges, then set the start node.
3. Click **▶ Run workflow**. The canvas colors the active node while it's being evaluated,
   then colors the whole path green/red as each YES/NO comes back, and the traversed edges
   get a thicker line. The execution log panel on the right shows each step's prompt and
   result as it happens.
4. **Export JSON** / **Import JSON** to save and reload a workflow.

## Phase 4 polish - which 3+ were built

- **Visual execution state** - the currently-running node is highlighted amber; completed
  nodes are colored green/red by their YES/NO result; the traversed edges are thickened.
- **Execution logs panel** - a live, auto-updating list of every step: node, prompt, result,
  and any error - polling while a run is in progress, stopping once it finishes.
- **JSON export/import** - the whole graph round-trips through the same `Graph.to_dict()` /
  `Graph.from_dict()` used internally, so an imported file is validated the same way a
  hand-built graph is.
- **Error handling** - an invalid graph (a decision node missing a YES or NO edge, no start
  node, etc.) is rejected with a clear message *before* the Run button sends anything to
  Inngest or spends a model call. A model that won't answer YES/NO even after one repair
  attempt fails the run cleanly with a readable error, rather than hanging or crashing.

## Verification

This sandbox had no path to a real LLM provider or a running Inngest dev server, so instead
of skipping verification, every layer was tested against real (mocked, for the LLM) or actual
(for Flask/Dash) execution - see `tests/`:

- `test_graph.py` (6 tests) - the data model: validation rules, edge replacement, serialization round-trip
- `test_executor.py` (7 tests) - pure traversal logic: the spec's own YES/NO example, multi-hop
  chains, cycle protection (a graph that loops is caught by a step cap, not an infinite loop),
  invalid graphs rejected before any model call
- `test_llm.py` (5 tests) - the YES/NO caller against a mock OpenAI-compatible server: clean
  answers, answers extracted from a sentence, a garbled answer repaired on retry, and a truly
  unrepairable answer failing cleanly
- `test_ui_helpers.py` (6 tests) - the graph → Cytoscape element/coloring logic
- `test_inngest_function.py` (4 tests) - calls the **actual** `run_workflow` function body
  (via Inngest's own `Function._handler`) with a fake step-runner against the mock LLM server,
  proving the real production wiring works, not a reimplementation of it

Run them all:
```bash
python tests/test_graph.py
python tests/test_executor.py
python tests/test_llm.py
python tests/test_ui_helpers.py
python tests/test_inngest_function.py
```

The Flask+Dash+Inngest server itself was booted and confirmed serving a valid Dash layout,
a working `/health` check, a working `/api/runs/<id>` polling endpoint, and a responding
`/api/inngest` handler.

**Not yet run**: a real end-to-end pass through the actual Inngest dev server with a live
model - that needs `npx inngest-cli@latest dev` and a real provider key, neither available in
this environment. Do that yourself with the two-terminal setup above.
