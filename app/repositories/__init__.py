"""Hand-written persistence operations for generated ORM models."""

from app.repositories.base import AsyncCrudRepository, RepositoryValidationError
from app.repositories.models import (
    ALL_REPOSITORIES,
    bt_equity_curve_repository,
    bt_run_repository,
    bt_strategy_repository,
    bt_summary_repository,
    bt_trade_repository,
    market_adj_factor_repository,
    market_daily_bar_repository,
    market_instrument_repository,
    market_trade_calendar_repository,
    ops_ingestion_batch_repository,
)

__all__ = [
    "ALL_REPOSITORIES",
    "AsyncCrudRepository",
    "RepositoryValidationError",
    "bt_equity_curve_repository",
    "bt_run_repository",
    "bt_strategy_repository",
    "bt_summary_repository",
    "bt_trade_repository",
    "market_adj_factor_repository",
    "market_daily_bar_repository",
    "market_instrument_repository",
    "market_trade_calendar_repository",
    "ops_ingestion_batch_repository",
]
