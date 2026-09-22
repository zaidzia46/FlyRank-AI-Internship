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

## Status

Stage 3 commit — model output is parsed, validated, repaired once, and quarantined on a second
failure. Verified against a local mock model covering: malformed JSON that repairs
successfully, malformed JSON that never repairs (422 + quarantine line), and a valid-JSON
answer with a category outside the enum (correctly rejected). Timeouts, a real retry policy,
cost logging, and the kill switch come in the next commit.
