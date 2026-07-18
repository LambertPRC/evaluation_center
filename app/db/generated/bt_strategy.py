# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Index, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON, TEXT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .bt_run import BtRun


class BtStrategy(Base):
    __tablename__ = "bt_strategy"
    __table_args__ = (
        Index("idx_status", "status"),
        Index("uk_strategy_version", "strategy_code", "version", unique=True),
        {"comment": "回测策略定义和版本"},
    )

    id: Mapped[int] = mapped_column(BIGINT(20, unsigned=True), primary_key=True, autoincrement=True)
    strategy_code: Mapped[str] = mapped_column(
        VARCHAR(64, collation="utf8mb4_unicode_ci"), nullable=False, comment="稳定策略标识"
    )
    version: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"), nullable=False, comment="策略版本"
    )
    strategy_name: Mapped[str] = mapped_column(
        VARCHAR(128, collation="utf8mb4_unicode_ci"), nullable=False, comment="显示名称"
    )
    implementation: Mapped[str] = mapped_column(
        VARCHAR(255, collation="utf8mb4_unicode_ci"), nullable=False, comment="Python模块或类路径"
    )
    status: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"),
        nullable=False,
        server_default=text("'DRAFT'"),
        comment="DRAFT/ACTIVE/ARCHIVED",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    description: Mapped[Optional[str]] = mapped_column(
        TEXT(collation="utf8mb4_unicode_ci"), comment="策略说明"
    )
    default_parameters: Mapped[Optional[dict]] = mapped_column(JSON, comment="默认参数")

    bt_run: Mapped[list["BtRun"]] = relationship("BtRun", back_populates="strategy")
