import asyncio

from fastapi import APIRouter
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import Settings
from app.db.engine import DatabaseResources

router = APIRouter()


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/ready",
    tags=["system"],
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"}},
)
async def readiness(request: Request) -> JSONResponse:
    resources = getattr(request.app.state, "database", None)
    settings = getattr(request.app.state, "settings", None)
    if not isinstance(resources, DatabaseResources) or not isinstance(settings, Settings):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "not_configured"},
        )

    try:
        async with asyncio.timeout(settings.db_ready_timeout):
            async with resources.engine.connect() as connection:
                value = await connection.scalar(text("SELECT 1"))
        if value != 1:
            raise RuntimeError("unexpected readiness result")
    except (OSError, RuntimeError, SQLAlchemyError, TimeoutError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "unreachable"},
        )

    return JSONResponse(content={"status": "ok", "database": "reachable"})
