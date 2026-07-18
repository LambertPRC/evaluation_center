from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient
from starlette.requests import Request

from app.core.settings import Settings
from app.infra.http_client import get_http_client
from app.main import create_app


def unconfigured_settings() -> Settings:
    return Settings(
        db_user=None,
        db_password=None,
        http_timeout=12.5,
    )


def test_http_client_is_reused_and_closed_with_application() -> None:
    application = create_app(unconfigured_settings())
    injected_clients: list[AsyncClient] = []

    @application.get("/test/http-client")
    async def capture_http_client(
        client: Annotated[AsyncClient, Depends(get_http_client)],
    ) -> dict[str, bool]:
        injected_clients.append(client)
        return {"closed": client.is_closed}

    with TestClient(application) as test_client:
        shared_client = application.state.http_client

        first_response = test_client.get("/test/http-client")
        second_response = test_client.get("/test/http-client")

        assert isinstance(shared_client, AsyncClient)
        assert shared_client.timeout.connect == 12.5
        assert first_response.json() == {"closed": False}
        assert second_response.json() == {"closed": False}
        assert injected_clients == [shared_client, shared_client]

    assert shared_client.is_closed


def test_http_client_dependency_rejects_an_uninitialized_application() -> None:
    application = FastAPI()
    request = Request({"type": "http", "app": application})

    with pytest.raises(HTTPException) as exc_info:
        get_http_client(request)

    assert exc_info.value.status_code == 503
