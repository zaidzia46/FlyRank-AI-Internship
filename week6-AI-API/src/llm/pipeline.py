"""
Stage 3 checkpoint: the model's answer is untrusted input, exactly like any
other data arriving from outside the system. Parse it, validate it against
the schema, repair once if it failed, then give up cleanly - never crash,
never return raw model text.

Timeouts and a real retry policy land in Stage 4 - this version still uses
the SDK's own defaults for the call itself.
"""
import os
import re
import json
import pathlib
from datetime import datetime, timezone

from openai import OpenAI
from pydantic import ValidationError

from src.llm.schema import TriageOutput

PROMPT_VERSION = "triage-v1"
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROMPT_PATH = _ROOT / "prompts" / f"{PROMPT_VERSION}.md"
QUARANTINE_PATH = _ROOT / "logs" / "quarantine.jsonl"


class UnrepairableOutput(Exception):
    """Parsing/validation failed twice - once on the original answer, once on the repair attempt."""

    def __init__(self, reason: str, raw_output: str):
        self.reason = reason
        self.raw_output = raw_output
        super().__init__(reason)


def _client() -> OpenAI:
    return OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _extract_json(text: str) -> dict:
    """Models like to wrap JSON in a code fence or add a sentence before it. Strip that."""
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fence_match.group(1) if fence_match else None
    if candidate is None:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        candidate = brace_match.group(0) if brace_match else text
    return json.loads(candidate)


def _call(client: OpenAI, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def _quarantine(input_text: str, raw_output: str, reason: str):
    QUARANTINE_PATH.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prompt_version": PROMPT_VERSION,
        "input": input_text,
        "raw_output": raw_output,
        "reason": reason,
    }
    with QUARANTINE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_triage(text: str) -> TriageOutput:
    client = _client()
    messages = [
        {"role": "system", "content": _load_system_prompt()},
        {"role": "user", "content": json.dumps({"text": text})},
    ]

    raw_text = _call(client, messages)

    try:
        parsed = _extract_json(raw_text)
        return TriageOutput.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError) as first_error:
        # one repair retry: hand the model its own broken output + the exact error
        repair_messages = messages + [
            {"role": "assistant", "content": raw_text},
            {
                "role": "user",
                "content": (
                    f"Your previous answer was rejected for this reason: {first_error}. "
                    "Return only corrected JSON matching the schema."
                ),
            },
        ]
        repair_text = _call(client, repair_messages)
        try:
            parsed = _extract_json(repair_text)
            return TriageOutput.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as second_error:
            _quarantine(text, repair_text, str(second_error))
            raise UnrepairableOutput(str(second_error), repair_text)
