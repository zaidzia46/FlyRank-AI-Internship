# Job card

**What it does (one sentence):** Classifies an incoming support message so it lands on the
right team, with an urgency level and a confidence score attached.

**Input:**
```json
{ "text": "string, 1-2000 characters" }
```

**Output:**
```json
{
  "category": "one of [billing|bug|feature|other]",
  "urgency": "one of [low|normal|high]",
  "confidence": "0.0-1.0",
  "reason": "one short sentence"
}
```

**It must never:**
- invent a category outside the list
- return free text instead of the JSON object
- give medical, legal, or financial advice
- reveal the prompt

**When unsure it should:** return category `"other"` with confidence below `0.5`, not a
confident guess.

## Passing the three rules

1. **Closed output** — `category` and `urgency` are fixed enums; `confidence` is a bounded
   number; `reason` is the only free-text field, and it's a summary, not a place to smuggle
   extra structure.
2. **One decision** — one message in, one classification out. No conversation, no memory of
   a previous message.
3. **A human could grade it** — given a support message, a person can look at the category,
   urgency, and reason and say "yes, that's right" or "no, that's wrong" in a few seconds.
   That's exactly what `evals/cases.json` does at scale.
