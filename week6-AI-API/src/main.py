"""
FlyRank A17 - Put an LLM behind your API.

Run:
    uvicorn src.main:app --reload
"""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.routes.triage import router as triage_router

app = FastAPI(title="FlyRank A17 - triage endpoint")
app.include_router(triage_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """
    FastAPI's default for a bad request body is 422. The assignment wants
    400 with the offending field named, so input errors (checked before any
    model call) are clearly distinct from Stage 3's 422 (a model answer that
    failed validation even after a repair attempt).
    """
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = [str(x) for x in first.get("loc", []) if x != "body"]
    field = ".".join(loc) if loc else "body"
    return JSONResponse(
        status_code=400,
        content={"error": "invalid_input", "field": field, "message": first.get("msg", "invalid input")},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
