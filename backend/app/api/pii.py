from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.api.schemas.pii import (
    PiiDetectRequest,
    PiiDetectResponse,
    PiiRedactRequest,
    PiiRedactResponse,
)

router = APIRouter(prefix="/pii", tags=["pii"])

PII_NOT_IMPLEMENTED_MESSAGE = (
    "PII service integration pending. Wire backend.app.security.pii.service during the integration phase."
)


@router.post("/detect", response_model=PiiDetectResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def detect_pii(_payload: PiiDetectRequest) -> JSONResponse:
    # TODO: Delegate to backend.app.security.pii.service.detect once the engine is integrated.
    response = PiiDetectResponse(
        status="not_implemented",
        message=PII_NOT_IMPLEMENTED_MESSAGE,
        matches=[],
    )
    return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content=response.model_dump())


@router.post("/redact", response_model=PiiRedactResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def redact_pii(payload: PiiRedactRequest) -> JSONResponse:
    # TODO: Delegate to backend.app.security.pii.service.redact once the engine is integrated.
    response = PiiRedactResponse(
        status="not_implemented",
        message=PII_NOT_IMPLEMENTED_MESSAGE,
        redacted_text=payload.text,
        matches=[],
    )
    return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content=response.model_dump())
