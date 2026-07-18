# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DATE, ForeignKeyConstraint, text
from sqlalchemy.dialects.mysql import BIGINT, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .bt_run import BtRun


class BtEquityCurve(Base):
    __tablename__ = "bt_equity_curve"
    __table_args__ = (
        ForeignKeyConstraint(["run_id"], ["bt_run.id"], ondelete="CASCADE", name="fk_equity_run"),
        {"comment": "回测每日现金、持仓、市值和资金曲线"},
    )

    run_id: Mapped[int] = mapped_column(
        BIGINT(20, unsigned=True), primary_key=True, comment="回测ID"
    )
    trade_date: Mapped[datetime.date] = mapped_column(DATE, primary_key=True, comment="交易日期")
    cash: Mapped[decimal.Decimal] = mapped_column(DECIMAL(20, 4), nullable=False, comment="现金")
    position_qty: Mapped[int] = mapped_column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="持仓数量"
    )
    close_price: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(18, 6), nullable=False, comment="当日收盘价"
    )
    market_value: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, comment="持仓市值"
    )
    total_equity: Mapped[decimal.Decimal] = mapped_column(
        DECIMAL(20, 4), nullable=False, comment="总权益"
    )
    daily_return: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="当日收益率"
    )
    cumulative_return: Mapped[Optional[decimal.Decimal]] = mapped_column(
        DECIMAL(18, 10), comment="累计收益率"
    )
    drawdown: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(18, 10), comment="当前回撤")

    run: Mapped["BtRun"] = relationship("BtRun", back_populates="bt_equity_curve")
