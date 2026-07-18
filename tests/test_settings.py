import pytest
from pydantic import SecretStr

from app.core.settings import DatabaseConfigurationError, Settings


def test_database_urls_use_separate_drivers_and_hide_password() -> None:
    password = "p@ss:/#%word"
    settings = Settings(
        db_host="127.0.0.1",
        db_port=3306,
        db_name="agent",
        db_user="agent_user",
        db_password=SecretStr(password),
    )

    async_url = settings.database_url("asyncmy")
    sync_url = settings.database_url("pymysql")

    assert async_url.drivername == "mysql+asyncmy"
    assert sync_url.drivername == "mysql+pymysql"
    assert async_url.database == "agent"
    assert async_url.query == {"charset": "utf8mb4"}
    assert async_url.password == password
    assert password not in str(async_url)


def test_database_url_requires_credentials() -> None:
    settings = Settings(db_user=None, db_password=None)

    with pytest.raises(DatabaseConfigurationError):
        settings.database_url("asyncmy")
