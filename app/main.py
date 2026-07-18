from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import AsyncClient

from app.api.router import router as api_router
from app.core.settings import Settings, get_settings
from app.db.engine import (
    DatabaseResources,
    create_database_resources,
    dispose_database_resources,
)
from app.infra.http_client import create_http_client, dispose_http_client


def create_app(settings: Settings | None = None) -> FastAPI:
    application_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resources: DatabaseResources | None = None
        http_client: AsyncClient | None = None
        try:
            if application_settings.database_configured:
                resources = create_database_resources(application_settings)
            http_client = create_http_client(application_settings)

            application.state.settings = application_settings
            application.state.database = resources
            application.state.http_client = http_client
            yield
        finally:
            try:
                await dispose_http_client(http_client)
            finally:
                await dispose_database_resources(resources)

    application = FastAPI(
        title="Evaluation Center",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
