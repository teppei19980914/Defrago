"""GTDデータモデルのテスト."""

from study_python.gtd.models import (
    DelegationStatus,
    DoNowStatus,
    EnergyLevel,
    GtdItem,
    ItemStatus,
    Location,
    Tag,
    TaskStatus,
    TimeEstimate,
    get_status_enum_for_tag,
)


class TestEnums:
    """Enum定義のテスト."""

    def test_item_status_values(self):
        assert ItemStatus.INBOX.value == "inbox"
        assert ItemStatus.SOMEDAY.value == "someday"
        assert ItemStatus.REFERENCE.value == "reference"
        assert ItemStatus.TRASH.value == "trash"

    def test_tag_values(self):
        assert Tag.DELEGATION.value == "delegation"
        assert Tag.PROJECT.value == "project"
        assert Tag.DO_NOW.value == "do_now"
        assert Tag.TASK.value == "task"

    def test_delegation_status_values(self):
        assert DelegationStatus.NOT_STARTED.value == "not_started"
        assert DelegationStatus.WAITING.value == "waiting"
        assert DelegationStatus.DONE.value == "done"

    def test_do_now_status_values(self):
        assert DoNowStatus.NOT_STARTED.value == "not_started"
        assert DoNowStatus.DONE.value == "done"

    def test_task_status_values(self):
        assert TaskStatus.NOT_STARTED.value == "not_started"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.DONE.value == "done"

    def test_location_values(self):
        assert Location.DESK.value == "desk"
        assert Location.HOME.value == "home"
        assert Location.COMMUTE.value == "commute"

    def test_time_estimate_values(self):
        assert TimeEstimate.WITHIN_10MIN.value == "10min"
        assert TimeEstimate.WITHIN_30MIN.value == "30min"
        assert TimeEstimate.WITHIN_1HOUR.value == "1hour"

    def test_energy_level_values(self):
        assert EnergyLevel.LOW.value == "low"
        assert EnergyLevel.MEDIUM.value == "medium"
        assert EnergyLevel.HIGH.value == "high"


class TestGetStatusEnumForTag:
    """get_status_enum_for_tagのテスト."""

    def test_delegation_tag(self):
        assert get_status_enum_for_tag(Tag.DELEGATION) is DelegationStatus

    def test_do_now_tag(self):
        assert get_status_enum_for_tag(Tag.DO_NOW) is DoNowStatus

    def test_task_tag(self):
        assert get_status_enum_for_tag(Tag.TASK) is TaskStatus

    def test_project_tag_returns_none(self):
        assert get_status_enum_for_tag(Tag.PROJECT) is None


class TestGtdItem:
    """GtdItemデータクラスのテスト."""

    def test_default_creation(self):
        item = GtdItem(title="テスト")
        assert item.title == "テスト"
        assert item.item_status == ItemStatus.INBOX
        assert item.tag is None
        assert item.status is None
        assert item.locations == []
        assert item.time_estimate is None
        assert item.energy is None
        assert item.note == ""
        assert item.deleted_at == ""
        assert item.id
        assert item.created_at
        assert item.updated_at

    def test_touch_updates_timestamp(self):
        item = GtdItem(title="テスト")
        old_updated = item.updated_at
        item.touch()
        assert item.updated_at >= old_updated

    def test_is_classified_false_when_no_tag(self):
        item = GtdItem(title="テスト")
        assert item.is_classified() is False

    def test_is_classified_true_when_tag_set(self):
        item = GtdItem(title="テスト", tag=Tag.TASK)
        assert item.is_classified() is True

    def test_is_done_false_when_no_tag(self):
        item = GtdItem(title="テスト")
        assert item.is_done() is False

    def test_is_done_false_when_not_completed(self):
        item = GtdItem(
            title="テスト", tag=Tag.TASK, status=TaskStatus.IN_PROGRESS.value
        )
        assert item.is_done() is False

    def test_is_done_true_when_completed(self):
        item = GtdItem(title="テスト", tag=Tag.TASK, status=TaskStatus.DONE.value)
        assert item.is_done() is True

    def test_is_done_true_delegation_done(self):
        item = GtdItem(
            title="テスト", tag=Tag.DELEGATION, status=DelegationStatus.DONE.value
        )
        assert item.is_done() is True

    def test_is_done_true_do_now_done(self):
        item = GtdItem(title="テスト", tag=Tag.DO_NOW, status=DoNowStatus.DONE.value)
        assert item.is_done() is True

    def test_is_done_false_for_project(self):
        item = GtdItem(title="テスト", tag=Tag.PROJECT)
        assert item.is_done() is False

    def test_needs_review_false_when_not_done(self):
        item = GtdItem(
            title="テスト", tag=Tag.TASK, status=TaskStatus.NOT_STARTED.value
        )
        assert item.needs_review() is False

    def test_needs_review_true_when_done(self):
        item = GtdItem(title="テスト", tag=Tag.TASK, status=TaskStatus.DONE.value)
        assert item.needs_review() is True

    def test_needs_review_true_for_project(self):
        item = GtdItem(title="テスト", tag=Tag.PROJECT)
        assert item.needs_review() is True

    def test_needs_review_false_for_trash_even_if_done(self):
        item = GtdItem(
            title="テスト",
            tag=Tag.TASK,
            status=TaskStatus.DONE.value,
            item_status=ItemStatus.TRASH,
        )
        assert item.needs_review() is False

    def test_is_in_trash_true(self):
        item = GtdItem(title="テスト", item_status=ItemStatus.TRASH)
        assert item.is_in_trash() is True

    def test_is_in_trash_false(self):
        item = GtdItem(title="テスト")
        assert item.is_in_trash() is False

    def test_default_parent_project_fields(self):
        item = GtdItem(title="テスト")
        assert item.parent_project_id is None
        assert item.parent_project_title == ""
        assert item.order is None

    def test_parent_project_fields_set(self):
        item = GtdItem(
            title="サブタスク",
            parent_project_id="proj-123",
            parent_project_title="大きなPJ",
            order=2,
        )
        assert item.parent_project_id == "proj-123"
        assert item.parent_project_title == "大きなPJ"
        assert item.order == 2
