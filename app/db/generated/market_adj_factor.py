# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
import decimal
from typing import TYPE_CHECKING

from sqlalchemy import DATE, ForeignKeyConstraint, Index, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, DECIMAL, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .market_instrument import MarketInstrument


class MarketAdjFactor(Base):
    __tablename__ = "market_adj_factor"
    __table_args__ = (
        ForeignKeyConstraint(
            ["instrument_id"], ["market_instrument.id"], name="fk_adj_factor_instrument"
        ),
        Index("idx_trade_date", "trade_date"),
        {"comment": "股票及基金复权因子"},
    )

    instrument_id: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), primary_key=True, comment="标的ID"
    )
    trade_date: Mapped[datetime.date] = mapped_column(DATE, primary_key=True, comment="交易日期")
    adj_factor: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(24, 10), nullable=False, comment="复权因子"
    )
    source: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"), nullable=False, comment="数据来源"
    )
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    instrument: Mapped["MarketInstrument"] = relationship(
        "MarketInstrument", back_populates="market_adj_factor"
    )
