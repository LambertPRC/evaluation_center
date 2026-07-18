# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DATE, ForeignKeyConstraint, Index, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, DECIMAL, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .market_instrument import MarketInstrument


class MarketDailyBar(Base):
    __tablename__ = "market_daily_bar"
    __table_args__ = (
        ForeignKeyConstraint(
            ["instrument_id"], ["market_instrument.id"], name="fk_daily_bar_instrument"
        ),
        Index("idx_trade_date", "trade_date"),
        {"comment": "未复权日线行情"},
    )

    instrument_id: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), primary_key=True, comment="标的ID"
    )
    trade_date: Mapped[datetime.date] = mapped_column(DATE, primary_key=True, comment="交易日期")
    open_price: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(18, 6), nullable=False, comment="开盘价，未复权"
    )
    high_price: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(18, 6), nullable=False, comment="最高价，未复权"
    )
    low_price: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(18, 6), nullable=False, comment="最低价，未复权"
    )
    close_price: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(18, 6), nullable=False, comment="收盘价，未复权"
    )
    is_suspended: Mapped[int] = mapped_column(
        TINYINT(1), nullable=False, server_default=text("'0'"), comment="是否停牌"
    )
    source: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"), nullable=False, comment="数据来源"
    )
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment="本地入库时间"
    )
    previous_close: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 6), comment="昨收价"
    )
    volume: Mapped[Optional[int]] = mapped_column(
        BIGINT(20, unsigned=True), comment="成交量，统一为股"
    )
    turnover: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(24, 4), comment="成交额，统一为元"
    )
    source_updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DATETIME, comment="供应商数据更新时间"
    )

    instrument: Mapped["MarketInstrument"] = relationship(
        "MarketInstrument", back_populates="market_daily_bar"
    )
