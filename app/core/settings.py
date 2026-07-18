"""Validated application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class DatabaseConfigurationError(RuntimeError):
    """Raised when a database operation is requested without credentials."""


class Settings(BaseSettings):
    """Runtime configuration.

    Credentials remain optional so liveness checks can run before a local
    database account has been configured. Database operations fail closed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_host: str = "127.0.0.1"
    db_port: int = Field(default=3306, ge=1, le=65535)
    db_name: str = "agent"
    db_user: str | None = None
    db_password: SecretStr | None = None
    db_charset: str = "utf8mb4"
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)
    db_pool_timeout: float = Field(default=10.0, gt=0)
    db_pool_recycle: int = Field(default=1800, ge=1)
    db_connect_timeout: int = Field(default=5, ge=1)
    db_ready_timeout: float = Field(default=3.0, gt=0)
    db_echo: bool = False

    @field_validator("db_host", "db_name", "db_charset")
    @classmethod
    def value_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    @field_validator("db_user")
    @classmethod
    def normalize_optional_user(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @property
    def database_configured(self) -> bool:
        return self.db_user is not None and self.db_password is not None

    def database_url(self, driver: Literal["asyncmy", "pymysql"]) -> URL:
        if not self.database_configured:
            raise DatabaseConfigurationError(
                "DB_USER and DB_PASSWORD must be configured for database access"
            )

        assert self.db_user is not None
        assert self.db_password is not None
        return URL.create(
            drivername=f"mysql+{driver}",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": self.db_charset},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
