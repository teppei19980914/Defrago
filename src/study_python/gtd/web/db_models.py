"""SQLAlchemy ORMモデル."""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from study_python.gtd.web.database import Base


class UserRow(Base):
    """ユーザーのDBテーブル定義."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)


class GtdItemRow(Base):
    """GTDアイテムのDBテーブル定義."""

    __tablename__ = "gtd_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")

    # 収集フェーズ
    item_status: Mapped[str] = mapped_column(String(20), default="inbox")

    # 明確化フェーズ
    tag: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # タスクContext
    locations_json: Mapped[str] = mapped_column(Text, default="[]")
    time_estimate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    energy: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # 整理フェーズ
    importance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    urgency: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # プロジェクト計画（ナチュラル・プランニング・モデル）
    project_purpose: Mapped[str] = mapped_column(Text, default="")
    project_outcome: Mapped[str] = mapped_column(Text, default="")
    project_support_location: Mapped[str] = mapped_column(Text, default="")
    is_next_action: Mapped[bool] = mapped_column(default=False)
    deadline: Mapped[str] = mapped_column(String(50), default="")

    # プロジェクト分解
    parent_project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    parent_project_title: Mapped[str] = mapped_column(String(500), default="")
    order: Mapped[int | None] = mapped_column("item_order", Integer, nullable=True)
