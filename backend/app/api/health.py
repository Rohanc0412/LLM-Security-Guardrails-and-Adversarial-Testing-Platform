from fastapi import APIRouter, Request

from backend.app.api.schemas.health import HealthResponse
from backend.app.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Application health status")
async def health_check(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.name,
        version=settings.version,
        environment=settings.env,
        dependencies={
            "database": bool(settings.database_url),
            "redis": bool(settings.redis_url),
        },
    )
