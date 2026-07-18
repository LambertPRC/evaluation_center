"""Reusable asynchronous CRUD operations for SQLAlchemy ORM models.

Repositories deliberately flush writes without committing them.  The caller owns
the transaction so several repository operations can be committed or rolled back
as one unit.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapper

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class RepositoryValidationError(ValueError):
    """Raised before database access when repository input is invalid."""


class AsyncCrudRepository(Generic[ModelT]):
    """Type-aware CRUD operations for one mapped SQLAlchemy model."""

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model
        self._mapper = cast(Mapper[ModelT], sqlalchemy_inspect(model))
        self._column_names = frozenset(attribute.key for attribute in self._mapper.column_attrs)
        self._primary_key_names = tuple(
            cast(str, column.key) for column in self._mapper.primary_key
        )

    @property
    def column_names(self) -> frozenset[str]:
        """Return column-backed attribute names accepted by create and filters."""

        return self._column_names

    @property
    def primary_key_names(self) -> tuple[str, ...]:
        """Return primary-key attribute names in mapper-defined order."""

        return self._primary_key_names

    async def create(
        self,
        session: AsyncSession,
        values: Mapping[str, Any],
    ) -> ModelT:
        """Create and flush an instance, then load database-generated values."""

        validated_values = self._validate_column_values(values, operation="create")
        instance = self.model(**validated_values)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def get(
        self,
        session: AsyncSession,
        identity: object,
    ) -> ModelT | None:
        """Return one instance by scalar, tuple, or mapping primary-key identity."""

        normalized_identity = self._normalize_identity(identity)
        return await session.get(self.model, normalized_identity)

    async def list(
        self,
        session: AsyncSession,
        *,
        filters: Mapping[str, Any] | None = None,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[ModelT]:
        """List rows using equality filters and stable primary-key ordering."""

        if offset < 0:
            raise RepositoryValidationError("offset must be greater than or equal to zero")
        if limit is not None and limit <= 0:
            raise RepositoryValidationError("limit must be greater than zero or None")

        validated_filters = self._validate_column_values(filters or {}, operation="filter")
        statement = (
            select(self.model)
            .filter_by(**validated_filters)
            .order_by(*self._mapper.primary_key)
            .offset(offset)
        )
        if limit is not None:
            statement = statement.limit(limit)

        result = await session.scalars(statement)
        return list(result.all())

    async def update(
        self,
        session: AsyncSession,
        identity: object,
        values: Mapping[str, Any],
    ) -> ModelT | None:
        """Update mutable columns and return the refreshed instance if it exists."""

        if not values:
            raise RepositoryValidationError("update requires at least one field")
        validated_values = self._validate_column_values(
            values,
            operation="update",
            allow_primary_keys=False,
        )
        normalized_identity = self._normalize_identity(identity)
        instance = await session.get(self.model, normalized_identity)
        if instance is None:
            return None

        for name, value in validated_values.items():
            setattr(instance, name, value)

        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(
        self,
        session: AsyncSession,
        identity: object,
    ) -> bool:
        """Delete by primary key and return whether a row was affected.

        An ORM-enabled DELETE is used instead of ``session.delete(instance)`` so
        database-level ON DELETE rules remain authoritative for generated models.
        """

        normalized_identity = self._normalize_identity(identity)
        predicates = (
            getattr(self.model, name) == value for name, value in normalized_identity.items()
        )
        statement = (
            sqlalchemy_delete(self.model)
            .where(*predicates)
            .execution_options(synchronize_session="fetch")
        )
        result = cast(CursorResult[Any], await session.execute(statement))
        return result.rowcount > 0

    def _validate_column_values(
        self,
        values: Mapping[str, Any],
        *,
        operation: str,
        allow_primary_keys: bool = True,
    ) -> dict[str, Any]:
        validated_values = dict(values)
        unknown_names = set(validated_values) - self._column_names
        if unknown_names:
            names = ", ".join(sorted(str(name) for name in unknown_names))
            raise RepositoryValidationError(
                f"{self.model.__name__} {operation} contains unknown columns: {names}"
            )

        if not allow_primary_keys:
            primary_key_names = set(validated_values) & set(self._primary_key_names)
            if primary_key_names:
                names = ", ".join(sorted(primary_key_names))
                raise RepositoryValidationError(
                    f"{self.model.__name__} primary keys cannot be updated: {names}"
                )
        return validated_values

    def _normalize_identity(self, identity: object) -> dict[str, Any]:
        if isinstance(identity, Mapping):
            identity_values = dict(identity)
            supplied_names = set(identity_values)
            expected_names = set(self._primary_key_names)
            if supplied_names != expected_names:
                missing = expected_names - supplied_names
                extra = supplied_names - expected_names
                details: list[str] = []
                if missing:
                    details.append(f"missing {', '.join(sorted(missing))}")
                if extra:
                    details.append(f"unexpected {', '.join(sorted(str(name) for name in extra))}")
                raise RepositoryValidationError(
                    f"invalid {self.model.__name__} primary key: {'; '.join(details)}"
                )
            return {name: identity_values[name] for name in self._primary_key_names}

        if len(self._primary_key_names) == 1:
            if isinstance(identity, tuple):
                if len(identity) != 1:
                    raise RepositoryValidationError(
                        f"{self.model.__name__} requires one primary-key value"
                    )
                identity = identity[0]
            return {self._primary_key_names[0]: identity}

        if not isinstance(identity, tuple) or len(identity) != len(self._primary_key_names):
            raise RepositoryValidationError(
                f"{self.model.__name__} requires {len(self._primary_key_names)} "
                "primary-key values as a tuple or mapping"
            )
        return dict(zip(self._primary_key_names, identity, strict=True))
