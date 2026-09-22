"""
The six lines from the assignment, made real:
  build the prompt -> call the model, with timeout + retries on the right
  errors only -> parse + validate the output -> repair once if it failed
  -> return clean JSON, or raise for the route to turn into a 422/504/502.

Never returns raw model text - callers only ever get a validated TriageOutput
or one of the exceptions below.
"""
import os
import re
import json
import time
import random
import pathlib
from datetime import datetime, timezone

from openai import (
    OpenAI,
    APITimeoutError,
    RateLimitError,
    APIStatusError,
)
from pydantic import ValidationError

from src.llm.schema import TriageOutput

PROMPT_VERSION = "triage-v1"
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROMPT_PATH = _ROOT / "prompts" / f"{PROMPT_VERSION}.md"
QUARANTINE_PATH = _ROOT / "logs" / "quarantine.jsonl"

DEFAULT_TIMEOUT_SECONDS = 30.0  # SDK default is 10 minutes - far too long for an HTTP endpoint
MAX_RETRIES = 2  # retries on timeout / 429 / 5xx only; never on 400 / 401 / 403


class ModelTimeout(Exception):
    """The model call timed out even after retries."""


class ModelUnavailable(Exception):
    """The provider returned an error that retrying won't fix (or retries were exhausted)."""


class UnrepairableOutput(Exception):
    """Parsing/validation failed twice - once on the original answer, once on the repair attempt."""

    def __init__(self, reason: str, raw_output: str):
        self.reason = reason
        self.raw_output = raw_output
        super().__init__(reason)


def _client(timeout_seconds: float | None = None) -> OpenAI:
    # read the module global at call time (not as a default-arg binding) so
    # tests and callers can override DEFAULT_TIMEOUT_SECONDS at runtime
    if timeout_seconds is None:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=timeout_seconds,
        max_retries=0,  # the SDK retries twice by default - we replace that with our own policy below
    )


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


def _backoff_seconds(attempt: int) -> float:
    """Exponential backoff with jitter: ~1s, ~2s, ~4s, plus a little randomness."""
    return (1.0 * (2 ** attempt)) + random.uniform(0, 0.5)


def _retry_after_seconds(exc) -> float | None:
    try:
        value = exc.response.headers.get("retry-after")
        return float(value) if value is not None else None
    except Exception:
        return None


def _call_with_retry(client: OpenAI, messages: list[dict]):
    """Yes on timeout / 429 / 5xx. Never on 400 / 401 / 403 - those won't fix themselves."""
    attempt = 0
    while True:
        start = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                messages=messages,
                temperature=0.2,  # low - we want the same answer for the same input, not creativity
            )
            duration_ms = round((time.monotonic() - start) * 1000)
            return response, duration_ms
        except APITimeoutError as exc:
            if attempt >= MAX_RETRIES:
                raise ModelTimeout("model call timed out after retries") from exc
            time.sleep(_backoff_seconds(attempt))
            attempt += 1
        except RateLimitError as exc:
            if attempt >= MAX_RETRIES:
                raise ModelUnavailable(f"rate limited after retries: {exc}") from exc
            time.sleep(_retry_after_seconds(exc) or _backoff_seconds(attempt))
            attempt += 1
        except APIStatusError as exc:
            status = exc.status_code
            if status is not None and 500 <= status < 600 and attempt < MAX_RETRIES:
                time.sleep(_backoff_seconds(attempt))
                attempt += 1
                continue
            # 400 / 401 / 403 / 404 and exhausted 5xx all land here - never retried further
            raise ModelUnavailable(f"upstream error {status}: {exc}") from exc


def _log_call(response, duration_ms: int, repaired: bool):
    usage = getattr(response, "usage", None)
    line = {
        "event": "llm_call",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prompt_version": PROMPT_VERSION,
        "model": os.environ.get("LLM_MODEL"),
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "duration_ms": duration_ms,
        "repaired": repaired,
    }
    print(json.dumps(line))  # structured log line to stdout - twelve-factor style, no log file to invent


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
    system_prompt = _load_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        # user content is JSON-encoded and sent as its own message - never glued
        # into the system prompt, so it can't break out of its own quotes.
        {"role": "user", "content": json.dumps({"text": text})},
    ]

    response, duration_ms = _call_with_retry(client, messages)
    raw_text = response.choices[0].message.content or ""

    try:
        parsed = _extract_json(raw_text)
        result = TriageOutput.model_validate(parsed)
        _log_call(response, duration_ms, repaired=False)
        return result
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
        try:
            repair_response, repair_duration_ms = _call_with_retry(client, repair_messages)
        except (ModelTimeout, ModelUnavailable):
            _quarantine(text, raw_text, f"repair call itself failed after: {first_error}")
            raise UnrepairableOutput(str(first_error), raw_text)

        repair_text = repair_response.choices[0].message.content or ""
        try:
            parsed = _extract_json(repair_text)
            result = TriageOutput.model_validate(parsed)
            _log_call(repair_response, repair_duration_ms, repaired=True)
            return result
        except (json.JSONDecodeError, ValidationError) as second_error:
            _quarantine(text, repair_text, str(second_error))
            raise UnrepairableOutput(str(second_error), repair_text)
