"""FastAPI dependencies for the application-scoped HTTP client."""

from fastapi import HTTPException, Request, status
from httpx import AsyncClient


def get_http_client(request: Request) -> AsyncClient:
    """Return the HTTP client initialized by the application lifespan."""

    client = getattr(request.app.state, "http_client", None)
    if not isinstance(client, AsyncClient) or client.is_closed:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HTTP client is not configured",
        )
    return client
