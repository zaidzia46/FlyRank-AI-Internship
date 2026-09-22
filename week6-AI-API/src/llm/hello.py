"""
Stage 0 checkpoint: prove one sentence can be gotten out of a model, from
your own machine. Throwaway - deleted once Stage 2 wires up the real prompt.

Run:
    python -m src.llm.hello
"""
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],  # OpenRouter: https://openrouter.ai/api/v1
    api_key=os.environ["LLM_API_KEY"],    # Ollama: the literal string "ollama"
)

response = client.chat.completions.create(
    model=os.environ["LLM_MODEL"],  # "openrouter/free" or "gemma3:1b"
    messages=[{"role": "user", "content": "Reply with exactly the word: ready"}],
)

print(response.choices[0].message.content)
