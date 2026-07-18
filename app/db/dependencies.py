"""FastAPI dependencies for request-scoped database sessions."""

from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import DatabaseResources


def get_database_resources(request: Request) -> DatabaseResources:
    resources = getattr(request.app.state, "database", None)
    if not isinstance(resources, DatabaseResources):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        )
    return resources


async def get_db_session(
    resources: DatabaseResources = Depends(get_database_resources),
) -> AsyncIterator[AsyncSession]:
    async with resources.session_factory() as session:
        try:
            yield session
        except BaseException:
            await session.rollback()
            raise
