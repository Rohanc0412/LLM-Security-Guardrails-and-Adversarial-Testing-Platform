from functools import lru_cache
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.schemas.pii import (
    PiiDetectRequest,
    PiiDetectResponse,
    PiiMatchResponse,
    PiiRedactRequest,
    PiiRedactResponse,
    PiiRedactionRecordResponse,
)
from backend.app.security.pii import PIIService
from backend.app.security.pii.models import PIIDetectionResult, PIIMatch, PIIRedactionResult, RedactionRecord

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pii", tags=["pii"])


def _build_pii_service() -> PIIService:
    return PIIService()


@lru_cache
def get_pii_service() -> PIIService:
    try:
        return _build_pii_service()
    except Exception as exc:
        logger.exception("Failed to initialize PII service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PII service unavailable",
        ) from exc


def _serialize_match(match: PIIMatch) -> PiiMatchResponse:
    return PiiMatchResponse(
        entity_type=match.entity_type,
        start=match.start,
        end=match.end,
        text=match.text,
        score=match.score,
        primary_source=match.primary_source.value,
        sources=[source.value for source in match.sources],
        source_metadata={key: dict(value) for key, value in match.source_metadata.items()},
    )


def _serialize_redaction(record: RedactionRecord) -> PiiRedactionRecordResponse:
    return PiiRedactionRecordResponse(
        entity_type=record.match.entity_type,
        start=record.match.start,
        end=record.match.end,
        strategy=record.strategy.value,
        replacement=record.replacement,
    )


def _serialize_detection_result(result: PIIDetectionResult) -> PiiDetectResponse:
    return PiiDetectResponse(
        status="ok",
        total_matches=result.total_matches,
        detectors_run=[source.value for source in result.detectors_run],
        matches=[_serialize_match(match) for match in result.matches],
    )


def _serialize_redaction_result(result: PIIRedactionResult) -> PiiRedactResponse:
    return PiiRedactResponse(
        status="ok",
        redacted_text=result.redacted_text,
        total_matches=len(result.matches),
        matches=[_serialize_match(match) for match in result.matches],
        redactions=[_serialize_redaction(record) for record in result.redactions],
    )


@router.post("/detect", response_model=PiiDetectResponse, summary="Detect PII in text")
async def detect_pii(
    payload: PiiDetectRequest,
    pii_service: PIIService = Depends(get_pii_service),
) -> PiiDetectResponse:
    try:
        return _serialize_detection_result(pii_service.detect(payload.text))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PII detection failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PII detection failed",
        ) from exc


@router.post("/redact", response_model=PiiRedactResponse, summary="Detect and redact PII in text")
async def redact_pii(
    payload: PiiRedactRequest,
    pii_service: PIIService = Depends(get_pii_service),
) -> PiiRedactResponse:
    try:
        return _serialize_redaction_result(
            pii_service.redact(payload.text, strategy_overrides=payload.strategy_overrides)
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PII redaction failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PII redaction failed",
        ) from exc
