import pytest

from automation.computer_task_contract import (
    ComputerTaskStatus,
    create_computer_task,
)


def test_factory_creates_valid_task_with_independent_defaults():
    first = create_computer_task("Open a document")
    second = create_computer_task("Open a browser")

    assert first.task_id
    assert first.task_id != second.task_id
    assert first.goal == "Open a document"
    assert first.status == ComputerTaskStatus.CREATED
    assert first.success_criteria == []
    assert first.constraints == []
    assert first.context == {}
    assert first.metadata == {}


def test_factory_strips_goal_and_optional_text():
    task = create_computer_task(
        "  Summarize a document  ",
        success_criteria=["  Include the main points  ", "", "  "],
        constraints=["  Do not modify the source  "],
        requested_result="  A short summary  ",
    )

    assert task.goal == "Summarize a document"
    assert task.success_criteria == ["Include the main points"]
    assert task.constraints == ["Do not modify the source"]
    assert task.requested_result == "A short summary"


def test_factory_rejects_empty_goal():
    with pytest.raises(ValueError, match="goal cannot be empty"):
        create_computer_task("   ")


def test_task_lifecycle_records_completion_result():
    task = create_computer_task("Open a document")

    task.start()
    assert task.status == ComputerTaskStatus.RUNNING
    assert task.started_at is not None

    task.complete({"opened": True})

    assert task.status == ComputerTaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.metadata["result"] == {"opened": True}


def test_task_failure_records_reason():
    task = create_computer_task("Open a document")

    task.start()
    task.fail("Target application was not found.")

    assert task.status == ComputerTaskStatus.FAILED
    assert task.completed_at is not None
    assert task.metadata["failure_reason"] == "Target application was not found."


def test_task_cancellation_records_reason():
    task = create_computer_task("Open a document")

    task.start()
    task.cancel("Cancelled by user.")

    assert task.status == ComputerTaskStatus.CANCELLED
    assert task.completed_at is not None
    assert task.metadata["cancel_reason"] == "Cancelled by user."


def test_serialization_contains_task_state():
    task = create_computer_task(
        "Search for documentation",
        success_criteria=["Return a source link"],
    )

    payload = task.to_dict()

    assert payload["goal"] == "Search for documentation"
    assert payload["status"] == ComputerTaskStatus.CREATED
    assert payload["success_criteria"] == ["Return a source link"]
    assert payload["task_id"] == task.task_id
