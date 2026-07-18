# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DATE, Index, text
from sqlalchemy.dialects.mysql import BIGINT, CHAR, DATETIME, INTEGER, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .bt_run import BtRun
    from .bt_trade import BtTrade
    from .market_adj_factor import MarketAdjFactor
    from .market_daily_bar import MarketDailyBar


class MarketInstrument(Base):
    __tablename__ = "market_instrument"
    __table_args__ = (
        Index("idx_type_status", "instrument_type", "status"),
        Index("uk_exchange_code", "exchange", "local_code", unique=True),
        Index("uk_symbol", "symbol", unique=True),
        {"comment": "证券、ETF、指数等标的基础信息"},
    )

    id: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), primary_key=True, autoincrement=True, comment="内部标的ID"
    )
    symbol: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"),
        nullable=False,
        comment="供应商标准代码，如510300.SH",
    )
    local_code: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"),
        nullable=False,
        comment="本地证券代码，如510300",
    )
    exchange: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"), nullable=False, comment="交易所：SSE/SZSE/BSE"
    )
    name: Mapped[str] = mapped_column(
        VARCHAR(128, collation="utf8mb4_unicode_ci"), nullable=False, comment="标的名称"
    )
    instrument_type: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"), nullable=False, comment="STOCK/ETF/INDEX/FUND"
    )
    currency: Mapped[str] = mapped_column(
        CHAR(3, collation="utf8mb4_unicode_ci"),
        nullable=False,
        server_default=text("'CNY'"),
        comment="交易币种",
    )
    lot_size: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True),
        nullable=False,
        server_default=text("'100'"),
        comment="最小交易单位",
    )
    status: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"),
        nullable=False,
        server_default=text("'ACTIVE'"),
        comment="ACTIVE/DELISTED/SUSPENDED",
    )
    source: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"), nullable=False, comment="标的信息来源"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    list_date: Mapped[Optional[datetime.date]] = mapped_column(DATE, comment="上市日期")
    delist_date: Mapped[Optional[datetime.date]] = mapped_column(DATE, comment="退市日期")

    bt_run: Mapped[list["BtRun"]] = relationship("BtRun", back_populates="instrument")
    market_adj_factor: Mapped[list["MarketAdjFactor"]] = relationship(
        "MarketAdjFactor", back_populates="instrument"
    )
    market_daily_bar: Mapped[list["MarketDailyBar"]] = relationship(
        "MarketDailyBar", back_populates="instrument"
    )
    bt_trade: Mapped[list["BtTrade"]] = relationship("BtTrade", back_populates="instrument")
