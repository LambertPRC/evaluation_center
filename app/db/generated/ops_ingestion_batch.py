# Generated from the MySQL schema by scripts/db_models.py.
# Do not edit generated files by hand; change the database and regenerate them.

import datetime
from typing import Optional

from sqlalchemy import DATE, Index, text
from sqlalchemy.dialects.mysql import BIGINT, CHAR, DATETIME, INTEGER, TEXT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OpsIngestionBatch(Base):
    __tablename__ = "ops_ingestion_batch"
    __table_args__ = (
        Index("idx_dataset_status", "dataset", "status"),
        Index("idx_started_at", "started_at"),
        Index("uk_batch_no", "batch_no", unique=True),
        {"comment": "外部市场数据采集批次记录"},
    )

    id: Mapped[int] = mapped_column(BIGINT(20, unsigned=True), primary_key=True, autoincrement=True)
    batch_no: Mapped[str] = mapped_column(
        CHAR(36, collation="utf8mb4_unicode_ci"), nullable=False, comment="批次UUID"
    )
    source: Mapped[str] = mapped_column(
        VARCHAR(32, collation="utf8mb4_unicode_ci"), nullable=False, comment="TUSHARE/AKSHARE等"
    )
    dataset: Mapped[str] = mapped_column(
        VARCHAR(64, collation="utf8mb4_unicode_ci"),
        nullable=False,
        comment="INSTRUMENT/DAILY_BAR/ADJ_FACTOR等",
    )
    status: Mapped[str] = mapped_column(
        VARCHAR(16, collation="utf8mb4_unicode_ci"),
        nullable=False,
        comment="RUNNING/SUCCESS/FAILED/PARTIAL",
    )
    requested_count: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True), nullable=False, server_default=text("'0'")
    )
    inserted_count: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True), nullable=False, server_default=text("'0'")
    )
    updated_count: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True), nullable=False, server_default=text("'0'")
    )
    rejected_count: Mapped[int] = mapped_column(
        INTEGER(10, unsigned=True), nullable=False, server_default=text("'0'")
    )
    started_at: Mapped[datetime.datetime] = mapped_column(DATETIME, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DATETIME, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    requested_start: Mapped[Optional[datetime.date]] = mapped_column(DATE, comment="请求开始日期")
    requested_end: Mapped[Optional[datetime.date]] = mapped_column(DATE, comment="请求结束日期")
    error_message: Mapped[Optional[str]] = mapped_column(TEXT(collation="utf8mb4_unicode_ci"))
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME)
