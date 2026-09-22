"""
Stage 1 checkpoint: the contract exists before the model does. Input is
validated by TriageInput before anything else happens - a wrong type,
missing field, or over-length text never reaches this far (FastAPI's
validation, converted to 400 by the handler in src/main.py, catches it
first). Stub mode returns a schema-valid response with zero model calls.

The real model call is wired up in Stage 2 - until then, an unstubbed
request returns 501 rather than pretending to call something that isn't
built yet.
"""
import os
from fastapi import APIRouter, HTTPException

from src.llm.schema import TriageInput, TriageOutput, STUB_RESPONSE

router = APIRouter()


@router.post("/triage", response_model=TriageOutput)
async def triage(payload: TriageInput):
    if os.environ.get("LLM_STUB") == "1":
        return STUB_RESPONSE

    raise HTTPException(
        status_code=501,
        detail="Model call not wired up yet - set LLM_STUB=1, or see Stage 2.",
    )
