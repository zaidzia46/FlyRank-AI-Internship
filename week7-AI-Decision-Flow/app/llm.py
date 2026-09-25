"""
Sends one decision-node prompt to the model and returns exactly "YES" or
"NO" - never anything else. The model's answer is untrusted input, same
principle as everywhere else in this program: validate it, repair once if
it's not clean, then fail loudly rather than guess.
"""
import os
import re
from openai import OpenAI

SYSTEM_PROMPT = (
    "You are a strict binary decision engine inside an automated workflow. "
    "You will be given a yes/no question about some input. "
    "Reply with exactly one word: YES or NO. "
    "No punctuation, no explanation, no other words - just YES or NO."
)


class DecisionError(Exception):
    """The model could not be made to answer with a clean YES/NO, even after one repair attempt."""


def _client() -> OpenAI:
    return OpenAI(
        base_url=os.environ.get("LLM_BASE_URL") or None,
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,
        max_retries=0,
    )


def _extract_yes_no(text: str) -> str | None:
    match = re.search(r"\b(YES|NO)\b", text.strip(), re.IGNORECASE)
    return match.group(1).upper() if match else None


def _ask(client: OpenAI, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content or ""


def ask_yes_no(prompt: str) -> str:
    """Returns 'YES' or 'NO'. Raises DecisionError if the model can't be made to answer cleanly."""
    client = _client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    raw = _ask(client, messages)
    result = _extract_yes_no(raw)
    if result:
        return result

    # one repair attempt: show the model its own answer and ask again, plainly
    repair_messages = messages + [
        {"role": "assistant", "content": raw},
        {"role": "user", "content": "That wasn't YES or NO. Reply with exactly one word: YES or NO."},
    ]
    raw_repair = _ask(client, repair_messages)
    result = _extract_yes_no(raw_repair)
    if result:
        return result

    raise DecisionError(f"model would not answer YES/NO after a repair attempt (last raw output: {raw_repair!r})")
