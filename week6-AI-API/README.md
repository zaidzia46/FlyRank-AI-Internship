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

## Status

Stage 0 commit — job card written, provider chosen and working, key safely in `.env`
(git-ignored) with `.env.example` committed alongside it. No endpoint yet.
