"""Repository instances for every generated ORM model."""

from typing import Any

from app.db.generated import (
    BtEquityCurve,
    BtRun,
    BtStrategy,
    BtSummary,
    BtTrade,
    MarketAdjFactor,
    MarketDailyBar,
    MarketInstrument,
    MarketTradeCalendar,
    OpsIngestionBatch,
)
from app.repositories.base import AsyncCrudRepository

bt_equity_curve_repository = AsyncCrudRepository(BtEquityCurve)
bt_run_repository = AsyncCrudRepository(BtRun)
bt_strategy_repository = AsyncCrudRepository(BtStrategy)
bt_summary_repository = AsyncCrudRepository(BtSummary)
bt_trade_repository = AsyncCrudRepository(BtTrade)
market_adj_factor_repository = AsyncCrudRepository(MarketAdjFactor)
market_daily_bar_repository = AsyncCrudRepository(MarketDailyBar)
market_instrument_repository = AsyncCrudRepository(MarketInstrument)
market_trade_calendar_repository = AsyncCrudRepository(MarketTradeCalendar)
ops_ingestion_batch_repository = AsyncCrudRepository(OpsIngestionBatch)

ALL_REPOSITORIES: tuple[AsyncCrudRepository[Any], ...] = (
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
