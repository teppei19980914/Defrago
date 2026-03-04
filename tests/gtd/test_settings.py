"""設定管理のテスト."""

from pathlib import Path

import pytest

from study_python.gtd.models import GtdItem, Tag
from study_python.gtd.settings import (
    STATUS_SORT_ORDER,
    TAG_SORT_ORDER,
    AppSettings,
    SettingsManager,
    SortCriterion,
    SortDirection,
    SortField,
    default_sort_criteria,
)


@pytest.fixture
def tmp_settings_path(tmp_path: Path) -> Path:
    return tmp_path / "test_settings.json"


@pytest.fixture
def mgr(tmp_settings_path: Path) -> SettingsManager:
    return SettingsManager(settings_path=tmp_settings_path)


class TestSortCriterion:
    """SortCriterionのテスト."""

    def test_default_values(self) -> None:
        c = SortCriterion()
        assert c.field == SortField.URGENCY
        assert c.direction == SortDirection.DESCENDING

    def test_custom_values(self) -> None:
        c = SortCriterion(field=SortField.TAG, direction=SortDirection.ASCENDING)
        assert c.field == SortField.TAG
        assert c.direction == SortDirection.ASCENDING


class TestDefaultSortCriteria:
    """default_sort_criteriaのテスト."""

    def test_returns_two_criteria(self) -> None:
        criteria = default_sort_criteria()
        assert len(criteria) == 2
        assert criteria[0].field == SortField.URGENCY
        assert criteria[0].direction == SortDirection.DESCENDING
        assert criteria[1].field == SortField.IMPORTANCE
        assert criteria[1].direction == SortDirection.DESCENDING


class TestAppSettings:
    """AppSettingsのテスト."""

    def test_default_settings(self) -> None:
        s = AppSettings()
        assert len(s.sort_criteria) == 2
        assert s.show_done_tasks is False


class TestSettingsManager:
    """SettingsManagerのテスト."""

    def test_init_default_path(self) -> None:
        mgr = SettingsManager()
        assert mgr.settings_path.name == "settings.json"

    def test_init_custom_path(self, tmp_settings_path: Path) -> None:
        mgr = SettingsManager(settings_path=tmp_settings_path)
        assert mgr.settings_path == tmp_settings_path

    def test_settings_property(self, mgr: SettingsManager) -> None:
        settings = mgr.settings
        assert isinstance(settings, AppSettings)

    def test_load_missing_file_returns_defaults(self, mgr: SettingsManager) -> None:
        settings = mgr.load()
        assert len(settings.sort_criteria) == 2
        assert settings.show_done_tasks is False

    def test_save_and_load_roundtrip(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [
                SortCriterion(SortField.TAG, SortDirection.ASCENDING),
                SortCriterion(SortField.URGENCY, SortDirection.DESCENDING),
            ]
        )
        mgr.update_show_done_tasks(True)
        mgr.save()

        mgr2 = SettingsManager(settings_path=mgr.settings_path)
        loaded = mgr2.load()
        assert len(loaded.sort_criteria) == 2
        assert loaded.sort_criteria[0].field == SortField.TAG
        assert loaded.sort_criteria[0].direction == SortDirection.ASCENDING
        assert loaded.sort_criteria[1].field == SortField.URGENCY
        assert loaded.sort_criteria[1].direction == SortDirection.DESCENDING
        assert loaded.show_done_tasks is True

    def test_load_corrupted_file(self, tmp_settings_path: Path) -> None:
        tmp_settings_path.write_text("not json", encoding="utf-8")
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert len(settings.sort_criteria) == 2

    def test_load_empty_criteria_uses_defaults(self, tmp_settings_path: Path) -> None:
        tmp_settings_path.write_text(
            '{"sort_criteria": [], "show_done_tasks": false}', encoding="utf-8"
        )
        mgr = SettingsManager(settings_path=tmp_settings_path)
        settings = mgr.load()
        assert len(settings.sort_criteria) == 2

    def test_update_sort_criteria_empty_raises(self, mgr: SettingsManager) -> None:
        with pytest.raises(ValueError, match="1つ以上必要"):
            mgr.update_sort_criteria([])

    def test_update_sort_criteria_duplicate_field_raises(
        self, mgr: SettingsManager
    ) -> None:
        with pytest.raises(ValueError, match="同じフィールドが複数"):
            mgr.update_sort_criteria(
                [
                    SortCriterion(SortField.URGENCY, SortDirection.DESCENDING),
                    SortCriterion(SortField.URGENCY, SortDirection.ASCENDING),
                ]
            )

    def test_update_sort_criteria_valid(self, mgr: SettingsManager) -> None:
        new_criteria = [SortCriterion(SortField.TAG, SortDirection.ASCENDING)]
        mgr.update_sort_criteria(new_criteria)
        assert mgr.settings.sort_criteria == new_criteria

    def test_update_show_done_tasks(self, mgr: SettingsManager) -> None:
        mgr.update_show_done_tasks(True)
        assert mgr.settings.show_done_tasks is True
        mgr.update_show_done_tasks(False)
        assert mgr.settings.show_done_tasks is False

    def test_save_creates_parent_directory(self, tmp_path: Path) -> None:
        nested_path = tmp_path / "nested" / "dir" / "settings.json"
        mgr = SettingsManager(settings_path=nested_path)
        mgr.save()
        assert nested_path.exists()


class TestSortItems:
    """SettingsManager.sort_items のテスト."""

    @staticmethod
    def _make_item(
        title: str,
        tag: Tag = Tag.TASK,
        status: str = "not_started",
        importance: int | None = None,
        urgency: int | None = None,
    ) -> GtdItem:
        return GtdItem(
            title=title,
            tag=tag,
            status=status,
            importance=importance,
            urgency=urgency,
        )

    def test_sort_by_importance_descending(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.IMPORTANCE, SortDirection.DESCENDING)]
        )
        items = [
            self._make_item("low", importance=2),
            self._make_item("high", importance=9),
            self._make_item("mid", importance=5),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["high", "mid", "low"]

    def test_sort_by_importance_ascending(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.IMPORTANCE, SortDirection.ASCENDING)]
        )
        items = [
            self._make_item("high", importance=9),
            self._make_item("low", importance=2),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["low", "high"]

    def test_sort_by_urgency_ascending(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.URGENCY, SortDirection.ASCENDING)]
        )
        items = [
            self._make_item("high_urg", urgency=9),
            self._make_item("low_urg", urgency=2),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["low_urg", "high_urg"]

    def test_sort_by_urgency_descending(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.URGENCY, SortDirection.DESCENDING)]
        )
        items = [
            self._make_item("low_urg", urgency=2),
            self._make_item("high_urg", urgency=9),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["high_urg", "low_urg"]

    def test_sort_by_tag_ascending(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.TAG, SortDirection.ASCENDING)]
        )
        items = [
            self._make_item("task", tag=Tag.TASK),
            self._make_item("do_now", tag=Tag.DO_NOW),
            self._make_item("delegation", tag=Tag.DELEGATION),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["do_now", "delegation", "task"]

    def test_sort_by_tag_descending(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.TAG, SortDirection.DESCENDING)]
        )
        items = [
            self._make_item("do_now", tag=Tag.DO_NOW),
            self._make_item("task", tag=Tag.TASK),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["task", "do_now"]

    def test_sort_by_status_ascending(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.STATUS, SortDirection.ASCENDING)]
        )
        items = [
            self._make_item("done", status="done"),
            self._make_item("not_started", status="not_started"),
            self._make_item("in_progress", status="in_progress"),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["not_started", "in_progress", "done"]

    def test_multi_criteria_sort(self, mgr: SettingsManager) -> None:
        """Primary: urgency desc, Secondary: importance desc."""
        mgr.update_sort_criteria(
            [
                SortCriterion(SortField.URGENCY, SortDirection.DESCENDING),
                SortCriterion(SortField.IMPORTANCE, SortDirection.DESCENDING),
            ]
        )
        items = [
            self._make_item("A", urgency=5, importance=3),
            self._make_item("B", urgency=8, importance=7),
            self._make_item("C", urgency=8, importance=9),
            self._make_item("D", urgency=5, importance=8),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["C", "B", "D", "A"]

    def test_sort_with_none_values(self, mgr: SettingsManager) -> None:
        mgr.update_sort_criteria(
            [SortCriterion(SortField.IMPORTANCE, SortDirection.DESCENDING)]
        )
        items = [
            self._make_item("no_imp", importance=None),
            self._make_item("has_imp", importance=5),
        ]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["has_imp", "no_imp"]

    def test_sort_empty_list(self, mgr: SettingsManager) -> None:
        result = mgr.sort_items([])
        assert result == []

    def test_sort_empty_criteria(self, mgr: SettingsManager) -> None:
        """空の条件リスト（直接設定）の場合は元の順序を保持."""
        mgr._settings.sort_criteria = []
        items = [self._make_item("A"), self._make_item("B")]
        result = mgr.sort_items(items)
        assert [r.title for r in result] == ["A", "B"]


class TestGetSortValue:
    """_get_sort_value のテスト."""

    def test_importance(self) -> None:
        item = GtdItem(title="t", importance=7)
        assert SettingsManager._get_sort_value(item, SortField.IMPORTANCE) == 7

    def test_importance_none(self) -> None:
        item = GtdItem(title="t", importance=None)
        assert SettingsManager._get_sort_value(item, SortField.IMPORTANCE) == 0

    def test_urgency(self) -> None:
        item = GtdItem(title="t", urgency=3)
        assert SettingsManager._get_sort_value(item, SortField.URGENCY) == 3

    def test_urgency_none(self) -> None:
        item = GtdItem(title="t", urgency=None)
        assert SettingsManager._get_sort_value(item, SortField.URGENCY) == 0

    def test_tag_known(self) -> None:
        item = GtdItem(title="t", tag=Tag.DO_NOW)
        val = SettingsManager._get_sort_value(item, SortField.TAG)
        assert val == TAG_SORT_ORDER[Tag.DO_NOW.value]

    def test_tag_none(self) -> None:
        item = GtdItem(title="t", tag=None)
        val = SettingsManager._get_sort_value(item, SortField.TAG)
        assert val == 999

    def test_status_known(self) -> None:
        item = GtdItem(title="t", status="in_progress")
        val = SettingsManager._get_sort_value(item, SortField.STATUS)
        assert val == STATUS_SORT_ORDER["in_progress"]

    def test_status_none(self) -> None:
        item = GtdItem(title="t", status=None)
        val = SettingsManager._get_sort_value(item, SortField.STATUS)
        assert val == 999
