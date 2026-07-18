from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router as api_router
from app.core.settings import Settings, get_settings
from app.db.engine import (
    DatabaseResources,
    create_database_resources,
    dispose_database_resources,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    application_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resources: DatabaseResources | None = None
        if application_settings.database_configured:
            resources = create_database_resources(application_settings)

        application.state.settings = application_settings
        application.state.database = resources
        try:
            yield
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
