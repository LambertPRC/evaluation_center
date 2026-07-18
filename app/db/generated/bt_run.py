# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DATE, ForeignKeyConstraint, Index, text
from sqlalchemy.dialects.mysql import BIGINT, CHAR, DATETIME, DECIMAL, JSON, TEXT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .bt_equity_curve import BtEquityCurve
    from .bt_strategy import BtStrategy
    from .bt_summary import BtSummary
    from .bt_trade import BtTrade
    from .market_instrument import MarketInstrument


class BtRun(Base):
    __tablename__ = "bt_run"
    __table_args__ = (
        ForeignKeyConstraint(["instrument_id"], ["market_instrument.id"], name="fk_run_instrument"),
        ForeignKeyConstraint(["strategy_id"], ["bt_strategy.id"], name="fk_run_strategy"),
        Index("idx_instrument_date", "instrument_id", "start_date", "end_date"),
        Index("idx_status_created", "status", "created_at"),
        Index("idx_strategy_created", "strategy_id", "created_at"),
        Index("uk_run_no", "run_no", unique=True),
        {"comment": "每次回测的配置、版本和执行状态"},
    )

    id: Mapped[int] = mapped_column(BIGINT(20, unsigned=True), primary_key=True, autoincrement=True)
    run_no: Mapped[str] = mapped_column(
        CHAR(36, collation="utf8mb4_unicode_ci"), nullable=False, comment="回测UUID"
    )
    strategy_id: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), nullable=False, comment="策略ID"
    )
    instrument_id: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), nullable=False, comment="MVP单标的"
    )
    start_date: Mapped[datetime.date] = mapped_column(DATE, nullable=False, comment="回测开始日期")
    end_date: Mapped[datetime.date] = mapped_column(DATE, nullable=False, comment="回测结束日期")
    initial_cash: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, comment="初始资金"
    )
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, comment="本次实际策略参数")
    commission_rate: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(12, 8), nullable=False, server_default=text("'0.00000000'"), comment="佣金率"
    )
    stamp_tax_rate: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(12, 8), nullable=False, server_default=text("'0.00000000'"), comment="印花税率"
    )
    slippage_rate: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(12, 8), nullable=False, server_default=text("'0.00000000'"), comment="滑点率"
    )
    execution_mode: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"),
        nullable=False,
        server_default=text("'NEXT_OPEN'"),
        comment="成交模型",
    )
    data_source: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"), nullable=False, comment="行情来源"
    )
    data_cutoff_time: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, comment="本次使用的数据截止时间"
    )
    status: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"),
        nullable=False,
        comment="PENDING/RUNNING/SUCCESS/FAILED",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    code_version: Mapped[Optional[str]] = mapped_column(
        VARCHAR(64, collation="utf8mb4_unicode_ci"), comment="Git commit或构建版本"
    )
    error_message: Mapped[Optional[str]] = mapped_column(TEXT(collation="utf8mb4_unicode_ci"))
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME)
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME)

    instrument: Mapped["MarketInstrument"] = relationship(
        "MarketInstrument", back_populates="bt_run"
    )
    strategy: Mapped["BtStrategy"] = relationship("BtStrategy", back_populates="bt_run")
    bt_equity_curve: Mapped[list["BtEquityCurve"]] = relationship(
        "BtEquityCurve", back_populates="run"
    )
    bt_summary: Mapped["BtSummary"] = relationship("BtSummary", uselist=False, back_populates="run")
    bt_trade: Mapped[list["BtTrade"]] = relationship("BtTrade", back_populates="run")
