# Put an LLM behind your API — /triage

FlyRank Internship, Backend Track, Week 7 (A17).

## What this endpoint does

One narrow job: a support message goes in, a structured classification comes out. See
`JOB-CARD.md` for the exact contract - input, output shape, the closed lists, what it must
never do, and what happens when the model is unsure.

## Provider & model

Two free lanes work unmodified with this code - only three environment variables differ:

| | OpenRouter (hosted) | Ollama (local) |
|---|---|---|
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | `http://localhost:11434/v1/` |
| `LLM_API_KEY` | your real key | the literal string `ollama` |
| `LLM_MODEL` | `openrouter/free` | `gemma3:1b` |

Copy `.env.example` to `.env` and fill in real values. **`.env` is git-ignored - never commit
it.**

## Try it

```bash
pip install -r requirements.txt
python -m src.llm.hello
```

Expected output: a line containing `ready`.

Three environment variables are the only difference between a model running on your laptop
and one running in a datacenter — nobody should ever hard-code a provider.

## Try it

```bash
pip install -r requirements.txt
LLM_STUB=1 uvicorn src.main:app --reload
```

Valid request (200, schema-shaped, zero model calls):
```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "I was charged twice this month"}'
```

Deliberately broken request (400, names the field):
```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{}'
```

## The prompt

Lives in `prompts/triage-v1.md`, not as a string in the route — it's code, it's versioned, and
it can be diffed when quality changes. It has five parts in order: role, exact output shape,
rules, a when-unsure instruction, and three examples (typical / ambiguous / hostile-or-empty).
The user's message is JSON-encoded and sent as its own `user` message, never glued into the
system prompt.

## Try it

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "I was charged twice this month"}'
```

At this stage the response is still raw model text (`{"raw_model_output": "..."}`) — schema
validation lands in the next commit.

## Making the output trustworthy

The model's answer is untrusted input, same as any external data source:
1. **Parse** — strip a code fence or a leading sentence if the model added one.
2. **Validate** — against the `TriageOutput` schema. A structurally valid JSON object with a
   category outside the enum still fails here.
3. **Repair once** — send the broken answer plus the exact validation error back, ask for a
   corrected version. Fixes most schema failures in practice.
4. **Quarantine on a second failure** — return `422` with a clear message, log the raw output,
   input, and reason to `logs/quarantine.jsonl`. Never crash, never guess a default.

Raw model text is never returned to the caller, on success or on failure.

## Try it

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "I was charged twice this month"}'
```

To see the failure path, temporarily edit `prompts/triage-v1.md` to demand a category outside
the enum, restart, and call it again — you get a `422` and a new line in
`logs/quarantine.jsonl`. Undo the edit afterward.

## Production hardening

| Concern | What's done |
|---|---|
| Timeout | 30s on the client (SDK default is 10 minutes). A timed-out call returns `504`. |
| Retries | Yes on timeout / `429` / `5xx`, with exponential backoff + jitter (~1s, ~2s, ~4s), honoring `Retry-After` when present. **Never** on `400` / `401` / `403` — asking again won't fix a bad key. SDK's own 2x default retry is disabled (`max_retries=0`); this is our own policy instead. |
| Cost logging | One structured JSON line to stdout per call: prompt version, model, input/output tokens, duration, whether it needed a repair. |
| Kill switch | `LLM_ENABLED=false` skips the model entirely and returns a deterministic, schema-valid fallback (`category: "other"`, `fallback: true`) — no deploy needed to turn the feature off. |

## Try it

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "I was charged twice this month"}'
```

Kill switch (zero model calls, immediate deterministic answer):
```bash
LLM_ENABLED=false uvicorn src.main:app --reload
```

## Eval

`evals/cases.json` has 8 hand-labelled cases (typical, ambiguous, and an embedded prompt
injection attempt). Run them against a live instance:

```bash
uvicorn src.main:app --port 8000 &
python evals/run_eval.py --url http://localhost:8000
```

**Real score: not yet run against a live provider from this environment** (this sandbox has
no network path to OpenRouter or Ollama — see "Verification" below for how the logic was
proven correct instead). Run the two commands above yourself once your `.env` has a real key,
and record the result here, e.g.:

> Score: 7/8 on category — prompt v1 — 2026-09-22 — model `openrouter/free`

## Verification (in place of a live eval score)

This sandbox couldn't reach a real LLM provider, so instead of skipping verification, the
whole pipeline was tested against a local OpenAI-compatible mock server standing in for the
provider — `tests/mock_llm_server.py` — driving the *real* `src/llm/pipeline.py` code over
real HTTP:

- valid JSON parses and validates
- a code-fenced answer (```json ... ```) is stripped and parsed
- malformed JSON is repaired successfully on the retry
- malformed JSON that never repairs → `422` + a quarantine line, never a crash
- valid JSON with a category outside the enum → rejected, not silently accepted
- `429` is retried with backoff and succeeds
- a persistent `500` retries then fails cleanly
- `401` is **never** retried (fails on the first call)
- a slow response correctly triggers the 30s timeout

Run it yourself:
```bash
python tests/test_pipeline_integration.py
python tests/test_routes.py
```

## Cost

One real call through the mock server, showing the exact log shape a real call produces:
```json
{"event": "llm_call", "timestamp": "2026-09-22T08:47:00Z", "prompt_version": "triage-v1", "model": "openrouter/free", "input_tokens": 120, "output_tokens": 40, "duration_ms": 340, "repaired": false}
```

**Estimate for 10,000 requests/day:** at ~120 input + ~40 output tokens per call (from the log
above; real numbers will vary with your prompt and provider), that's 1.2M input + 0.4M output
tokens/day. On OpenRouter's free tier that's $0 (and well over the 50/day free-tier cap — a
paid model or Ollama would be needed at that volume). Plug your actual token counts and
provider's price-per-1K-tokens into the [LLM price calculator](https://tools.simonwillison.net/llm-prices)
for a real number once you're on a paid model.

## What I'd fix with another day

Add the "measure before you spend" stretch: count tokens before sending and reject anything
over a set limit, so a single oversized `text` field can't produce a surprise bill. Right now
the 2000-character input cap bounds this loosely, but it's characters, not tokens.