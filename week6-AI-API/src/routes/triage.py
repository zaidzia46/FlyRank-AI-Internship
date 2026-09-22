"""
Stage 3 checkpoint: the endpoint's contract is the schema now - never raw
model text, on success or on failure.
"""
import os
from fastapi import APIRouter, HTTPException

from src.llm.schema import TriageInput, TriageOutput, STUB_RESPONSE
from src.llm import pipeline

router = APIRouter()


@router.post("/triage", response_model=TriageOutput)
async def triage(payload: TriageInput):
    if os.environ.get("LLM_STUB") == "1":
        return STUB_RESPONSE

    try:
        return pipeline.run_triage(payload.text)
    except pipeline.UnrepairableOutput as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Model output failed validation after one repair attempt: {exc.reason}",
        )
    except Exception as exc:  # timeout/retry policy still to come in Stage 4
        raise HTTPException(status_code=502, detail=f"Model call failed: {exc}")
