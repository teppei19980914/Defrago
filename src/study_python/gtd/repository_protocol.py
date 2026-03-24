"""GTDリポジトリのプロトコル定義.

ロジック層が依存するリポジトリインターフェースを定義する。
"""

from __future__ import annotations

from typing import Protocol

from study_python.gtd.models import GtdItem, ItemStatus, Tag


class GtdRepositoryProtocol(Protocol):
    """GTDリポジトリのプロトコル.

    ロジック層はこのプロトコルに依存し、
    具体的な永続化実装（JSON / SQLAlchemy）から分離する。
    """

    @property
    def items(self) -> list[GtdItem]: ...

    def add(self, item: GtdItem) -> None: ...

    def remove(self, item_id: str) -> GtdItem | None: ...

    def get(self, item_id: str) -> GtdItem | None: ...

    def get_by_status(self, status: ItemStatus) -> list[GtdItem]: ...

    def get_by_tag(self, tag: Tag) -> list[GtdItem]: ...

    def get_tasks(self) -> list[GtdItem]: ...
