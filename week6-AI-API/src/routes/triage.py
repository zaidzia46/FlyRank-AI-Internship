"""
POST /triage - one message in, one validated classification out.

Order of checks: stub mode, then the kill switch, then the real pipeline.
Both short-circuits return a schema-valid response with zero model calls.
"""
import os
from fastapi import APIRouter, HTTPException

from src.llm.schema import TriageInput, TriageOutput, STUB_RESPONSE, FALLBACK_RESPONSE
from src.llm import pipeline

router = APIRouter()


@router.post("/triage", response_model=TriageOutput)
async def triage(payload: TriageInput):
    if os.environ.get("LLM_STUB") == "1":
        return STUB_RESPONSE

    if os.environ.get("LLM_ENABLED", "true").lower() == "false":
        return FALLBACK_RESPONSE

    try:
        return pipeline.run_triage(payload.text)
    except pipeline.ModelTimeout:
        raise HTTPException(status_code=504, detail="The model took too long to respond.")
    except pipeline.UnrepairableOutput as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Model output failed validation after one repair attempt: {exc.reason}",
        )
    except pipeline.ModelUnavailable as exc:
        raise HTTPException(status_code=502, detail=f"Upstream model provider error: {exc}")
