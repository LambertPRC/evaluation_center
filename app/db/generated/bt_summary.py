# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKeyConstraint, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, DECIMAL, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .bt_run import BtRun


class BtSummary(Base):
    __tablename__ = "bt_summary"
    __table_args__ = (
        ForeignKeyConstraint(["run_id"], ["bt_run.id"], ondelete="CASCADE", name="fk_summary_run"),
        {"comment": "回测核心绩效指标汇总"},
    )

    run_id: Mapped[int] = mapped_column(BIGINT(20, unsigned=True), primary_key=True)
    final_equity: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, comment="期末总权益"
    )
    trade_count: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True), nullable=False, server_default=text("'0'"), comment="成交次数"
    )
    win_count: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True),
        nullable=False,
        server_default=text("'0'"),
        comment="盈利交易次数",
    )
    loss_count: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True),
        nullable=False,
        server_default=text("'0'"),
        comment="亏损交易次数",
    )
    total_commission: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, server_default=text("'0.0000'"), comment="累计佣金"
    )
    total_stamp_tax: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, server_default=text("'0.0000'"), comment="累计印花税"
    )
    total_slippage: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, server_default=text("'0.0000'"), comment="累计滑点"
    )
    trading_days: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True), nullable=False, server_default=text("'0'"), comment="交易日数"
    )
    calculated_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    total_return: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="累计收益率"
    )
    annualized_return: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="年化收益率"
    )
    benchmark_return: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="基准收益率"
    )
    annualized_volatility: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="年化波动率"
    )
    sharpe_ratio: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="夏普比率"
    )
    sortino_ratio: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="索提诺比率"
    )
    max_drawdown: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="最大回撤"
    )
    win_rate: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(18, 10), comment="胜率")
    turnover_rate: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="换手率"
    )

    run: Mapped["BtRun"] = relationship("BtRun", back_populates="bt_summary")
