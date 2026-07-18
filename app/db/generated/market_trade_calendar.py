# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
from typing import Optional

from sqlalchemy import DATE, Index, text
from sqlalchemy.dialects.mysql import DATETIME, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MarketTradeCalendar(Base):
    __tablename__ = "market_trade_calendar"
    __table_args__ = (
        Index("idx_open_date", "exchange", "is_open", "calendar_date"),
        {"comment": "各交易所交易日历"},
    )

    exchange: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"), primary_key=True, comment="交易所"
    )
    calendar_date: Mapped[datetime.date] = mapped_column(DATE, primary_key=True, comment="自然日期")
    is_open: Mapped[int] = mapped_column(TINYINT(1), nullable=False, comment="1开市，0休市")
    source: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"), nullable=False, comment="数据来源"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    previous_open_date: Mapped[Optional[datetime.date]] = mapped_column(
        DATE, comment="上一个交易日"
    )
    next_open_date: Mapped[Optional[datetime.date]] = mapped_column(DATE, comment="下一个交易日")
