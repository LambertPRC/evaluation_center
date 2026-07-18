import asyncio

from pydantic import SecretStr

from app.core.settings import Settings
from app.db.engine import create_database_resources, dispose_database_resources


def test_database_resources_are_created_without_opening_a_connection() -> None:
    settings = Settings(
        db_user="agent_user",
        db_password=SecretStr("not-used"),
    )

    resources = create_database_resources(settings)

    assert resources.engine.url.drivername == "mysql+asyncmy"
    assert resources.engine.url.database == "agent"
    asyncio.run(dispose_database_resources(resources))
