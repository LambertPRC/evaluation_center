"""Application-scoped asynchronous HTTP client lifecycle."""

from httpx import AsyncClient, Limits, Timeout

from app.core.settings import Settings


def create_http_client(settings: Settings) -> AsyncClient:
    """Create one client whose connection pool is shared by the application."""

    return AsyncClient(
        timeout=Timeout(settings.http_timeout),
        limits=Limits(
            max_connections=settings.http_max_connections,
            max_keepalive_connections=settings.http_max_keepalive_connections,
            keepalive_expiry=settings.http_keepalive_expiry,
        ),
    )


async def dispose_http_client(client: AsyncClient | None) -> None:
    """Close the shared client and all pooled connections."""

    if client is not None and not client.is_closed:
        await client.aclose()
