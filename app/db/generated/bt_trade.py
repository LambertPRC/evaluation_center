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
    from .bt_run import BtRun
    from .market_instrument import MarketInstrument


class BtTrade(Base):
    __tablename__ = "bt_trade"
    __table_args__ = (
        ForeignKeyConstraint(
            ["instrument_id"], ["market_instrument.id"], name="fk_trade_instrument"
        ),
        ForeignKeyConstraint(["run_id"], ["bt_run.id"], ondelete="CASCADE", name="fk_trade_run"),
        Index("idx_instrument_date", "instrument_id", "trade_date"),
        Index("idx_run_trade_date", "run_id", "trade_date"),
        {"comment": "回测产生的模拟成交明细"},
    )

    id: Mapped[int] = mapped_column(BIGINT(20, unsigned=True), primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(BIGINT(20, unsigned=True), nullable=False, comment="回测ID")
    instrument_id: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), nullable=False, comment="标的ID"
    )
    signal_date: Mapped[datetime.date] = mapped_column(DATE, nullable=False, comment="信号产生日期")
    trade_date: Mapped[datetime.date] = mapped_column(DATE, nullable=False, comment="模拟成交日期")
    side: Mapped[str] = mapped_column(
        VARCHAR(8, collation="utf8mb4_unicode_ci"), nullable=False, comment="BUY/SELL"
    )
    quantity: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), nullable=False, comment="成交数量"
    )
    raw_price: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(18, 6), nullable=False, comment="未计滑点价格"
    )
    executed_price: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(18, 6), nullable=False, comment="模拟成交价格"
    )
    gross_amount: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, comment="成交金额"
    )
    commission: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, server_default=text("'0.0000'"), comment="佣金"
    )
    stamp_tax: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, server_default=text("'0.0000'"), comment="印花税"
    )
    slippage_cost: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, server_default=text("'0.0000'"), comment="滑点成本"
    )
    total_cost: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, server_default=text("'0.0000'"), comment="总交易费用"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    instrument: Mapped["MarketInstrument"] = relationship(
        "MarketInstrument", back_populates="bt_trade"
    )
    run: Mapped["BtRun"] = relationship("BtRun", back_populates="bt_trade")
