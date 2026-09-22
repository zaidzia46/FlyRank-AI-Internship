"""
Stage 2 checkpoint: the prompt is a versioned file, wired to the endpoint.
The response is still raw model text at this point - deliberately, so this
stage's checkpoint is just "does a real model answer come back correctly
shaped for three different inputs?" Schema validation, repair, and
quarantine land in Stage 3.
"""
import os
from fastapi import APIRouter, HTTPException

from src.llm.schema import TriageInput, STUB_RESPONSE
from src.llm import pipeline

router = APIRouter()


@router.post("/triage")
async def triage(payload: TriageInput):
    if os.environ.get("LLM_STUB") == "1":
        return STUB_RESPONSE

    try:
        raw_text = pipeline.call_model_raw(payload.text)
    except Exception as exc:  # not yet a real retry/timeout policy - that's Stage 4
        raise HTTPException(status_code=502, detail=f"Model call failed: {exc}")

    # TEMPORARY - Stage 3 replaces this with parse + validate + repair.
    return {"raw_model_output": raw_text}
