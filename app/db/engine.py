"""Async SQLAlchemy engine and session-factory lifecycle."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import Settings


@dataclass(frozen=True, slots=True)
class DatabaseResources:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]


def create_database_resources(settings: Settings) -> DatabaseResources:
    engine = create_async_engine(
        settings.database_url("asyncmy"),
        echo=settings.db_echo,
        hide_parameters=True,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        connect_args={"connect_timeout": settings.db_connect_timeout},
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )
    return DatabaseResources(engine=engine, session_factory=session_factory)


async def dispose_database_resources(resources: DatabaseResources | None) -> None:
    if resources is not None:
        await resources.engine.dispose()
