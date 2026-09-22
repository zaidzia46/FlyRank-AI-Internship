from typing import Literal
from pydantic import BaseModel, Field

Category = Literal["billing", "bug", "feature", "other"]
Urgency = Literal["low", "normal", "high"]


class TriageInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class TriageOutput(BaseModel):
    category: Category
    urgency: Urgency
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., max_length=300)
    fallback: bool = False  # true only when the kill switch served this response


# Stage 1's stub mode: schema-valid, hard-coded, zero model calls.
STUB_RESPONSE = TriageOutput(
    category="feature",
    urgency="normal",
    confidence=0.42,
    reason="Stub mode - no model was called.",
    fallback=False,
)

# Stage 4's kill switch fallback: schema-valid, deterministic, zero model calls.
FALLBACK_RESPONSE = TriageOutput(
    category="other",
    urgency="low",
    confidence=0.0,
    reason="LLM disabled (LLM_ENABLED=false) - routed for manual review.",
    fallback=True,
)
