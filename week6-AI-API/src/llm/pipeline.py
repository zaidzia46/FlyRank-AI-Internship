"""
Stage 2 checkpoint: load the prompt file, call the model, return whatever
text comes back. No parsing, validation, or repair yet - that's Stage 3.

temperature is set low (0.2) because a classification task wants the same
answer for the same input, not creative variation.
"""
import os
import json
import pathlib
from openai import OpenAI

PROMPT_VERSION = "triage-v1"
PROMPT_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "prompts" / f"{PROMPT_VERSION}.md"


def _client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def call_model_raw(text: str) -> str:
    """Send the user's text as its own message - never glued into the system prompt."""
    client = _client()
    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {"role": "system", "content": _load_system_prompt()},
            {"role": "user", "content": json.dumps({"text": text})},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""
