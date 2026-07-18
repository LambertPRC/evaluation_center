import asyncio
import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy import Delete, Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.generated import Base, MarketDailyBar, MarketInstrument
from app.repositories import (
    ALL_REPOSITORIES,
    RepositoryValidationError,
    market_daily_bar_repository,
    market_instrument_repository,
)


def make_session_mock() -> Any:
    return MagicMock(spec=AsyncSession)


def instrument_values() -> dict[str, object]:
    return {
        "symbol": "510300.SH",
        "local_code": "510300",
        "exchange": "SSE",
        "name": "CSI 300 ETF",
        "instrument_type": "ETF",
        "source": "TEST",
    }


def test_every_generated_model_has_a_repository() -> None:
    mapped_models = {mapper.class_ for mapper in Base.registry.mappers}
    repository_models = {repository.model for repository in ALL_REPOSITORIES}

    assert repository_models == mapped_models
    assert len(ALL_REPOSITORIES) == 10


def test_create_adds_flushes_and_refreshes_without_committing() -> None:
    async def scenario() -> None:
        session = make_session_mock()

        instance = await market_instrument_repository.create(session, instrument_values())

        assert isinstance(instance, MarketInstrument)
        assert instance.symbol == "510300.SH"
        session.add.assert_called_once_with(instance)
        session.flush.assert_awaited_once_with()
        session.refresh.assert_awaited_once_with(instance)
        session.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_get_normalizes_a_composite_primary_key_mapping() -> None:
    async def scenario() -> None:
        session = make_session_mock()
        expected = MagicMock(spec=MarketDailyBar)
        session.get.return_value = expected
        trade_date = datetime.date(2026, 7, 18)

        actual = await market_daily_bar_repository.get(
            session,
            {"trade_date": trade_date, "instrument_id": 7},
        )

        assert actual is expected
        session.get.assert_awaited_once_with(
            MarketDailyBar,
            {"instrument_id": 7, "trade_date": trade_date},
        )

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "identity",
    [
        7,
        (7,),
        {"instrument_id": 7},
        {"instrument_id": 7, "trade_date": datetime.date(2026, 7, 18), "extra": 1},
    ],
)
def test_get_rejects_an_incomplete_or_invalid_composite_key(identity: object) -> None:
    async def scenario() -> None:
        session = make_session_mock()

        with pytest.raises(RepositoryValidationError):
            await market_daily_bar_repository.get(session, identity)

        session.get.assert_not_awaited()

    asyncio.run(scenario())


def test_list_uses_filters_and_returns_scalar_models() -> None:
    async def scenario() -> None:
        session = make_session_mock()
        expected = MarketInstrument(**instrument_values())
        scalar_result = MagicMock()
        scalar_result.all.return_value = [expected]
        session.scalars.return_value = scalar_result

        actual = await market_instrument_repository.list(
            session,
            filters={"status": "ACTIVE"},
            offset=5,
            limit=10,
        )

        assert actual == [expected]
        statement = session.scalars.await_args.args[0]
        assert isinstance(statement, Select)
        session.commit.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("offset", "limit"),
    [(-1, 10), (0, 0), (0, -1)],
)
def test_list_rejects_invalid_pagination(offset: int, limit: int) -> None:
    async def scenario() -> None:
        session = make_session_mock()

        with pytest.raises(RepositoryValidationError):
            await market_instrument_repository.list(session, offset=offset, limit=limit)

        session.scalars.assert_not_awaited()

    asyncio.run(scenario())


def test_update_changes_columns_flushes_and_refreshes_without_committing() -> None:
    async def scenario() -> None:
        session = make_session_mock()
        instance = MarketInstrument(id=7, **instrument_values())
        session.get.return_value = instance

        actual = await market_instrument_repository.update(
            session,
            7,
            {"name": "Updated ETF", "status": "SUSPENDED"},
        )

        assert actual is instance
        assert instance.name == "Updated ETF"
        assert instance.status == "SUSPENDED"
        session.get.assert_awaited_once_with(MarketInstrument, {"id": 7})
        session.flush.assert_awaited_once_with()
        session.refresh.assert_awaited_once_with(instance)
        session.commit.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize("values", [{}, {"id": 8}, {"bt_run": []}, {"unknown": "value"}])
def test_update_rejects_empty_primary_key_relationship_and_unknown_fields(
    values: dict[str, object],
) -> None:
    async def scenario() -> None:
        session = make_session_mock()

        with pytest.raises(RepositoryValidationError):
            await market_instrument_repository.update(session, 7, values)

        session.get.assert_not_awaited()
        session.flush.assert_not_awaited()

    asyncio.run(scenario())


def test_update_returns_none_when_the_row_does_not_exist() -> None:
    async def scenario() -> None:
        session = make_session_mock()
        session.get.return_value = None

        actual = await market_instrument_repository.update(session, 404, {"name": "missing"})

        assert actual is None
        session.flush.assert_not_awaited()
        session.refresh.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize(("rowcount", "expected"), [(1, True), (0, False)])
def test_delete_uses_primary_key_dml_without_committing(rowcount: int, expected: bool) -> None:
    async def scenario() -> None:
        session = make_session_mock()
        result = MagicMock()
        result.rowcount = rowcount
        session.execute.return_value = result

        actual = await market_daily_bar_repository.delete(
            session,
            (7, datetime.date(2026, 7, 18)),
        )

        assert actual is expected
        statement = session.execute.await_args.args[0]
        assert isinstance(statement, Delete)
        assert statement.get_execution_options()["synchronize_session"] == "fetch"
        session.commit.assert_not_awaited()

    asyncio.run(scenario())
