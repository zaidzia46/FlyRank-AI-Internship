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

## Status

Stage 2 commit — the prompt is a versioned file, wired to a real model call for three
different inputs. Not yet trustworthy: the model's answer is returned as-is, with no parsing,
validation, or repair. That's next.
