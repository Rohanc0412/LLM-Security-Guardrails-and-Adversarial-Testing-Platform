from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from backend.app.api.router import api_router
from backend.app.config import get_settings
from backend.app.database import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    redis_client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.redis = redis_client

    try:
        yield
    finally:
        await redis_client.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.name,
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
