"""Tests for sdd-util status command."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from click.testing import CliRunner

import sdd.util_cli as _util_mod
from sdd.util_cli import cli


@pytest.fixture
def patch_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provides a context that patches find_project_root."""
    def _set(root: Path) -> None:
        monkeypatch.setattr(_util_mod, "find_project_root", lambda: root)
    yield _set  # type: ignore[misc]


class TestStatusAllEpics:
    def test_no_epics(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "No epics found" in result.output

    def test_shows_all_epics(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "EPIC_001" in result.output
        assert "Checkout Resume" in result.output
        assert "STORY_001" in result.output
        assert "STORY_002" in result.output

    def test_shows_task_counts(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        # STORY_001 has 2 tasks, both TODO -> 0/2
        assert "0/2 tasks done" in result.output
        # STORY_002 has 1 task, TODO -> 0/1
        assert "0/1 tasks done" in result.output


class TestStatusEpic:
    def test_by_name(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "checkout"])
        assert result.exit_code == 0
        assert "EPIC_001" in result.output
        assert "Stories" in result.output

    def test_explicit_type(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "checkout", "--type", "epic"])
        assert result.exit_code == 0
        assert "EPIC_001" in result.output

    def test_not_found(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "nonexistent", "--type", "epic"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestStatusStory:
    def test_by_name(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "STORY_001", "--type", "story"])
        assert result.exit_code == 0
        assert "STORY_001" in result.output
        assert "TASK_001" in result.output
        assert "TASK_002" in result.output

    def test_shows_parent_epic(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "STORY_001", "--type", "story"])
        assert result.exit_code == 0
        assert "EPIC_001" in result.output

    def test_shows_task_statuses(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "STORY_001", "--type", "story"])
        assert result.exit_code == 0
        assert "TASK_001" in result.output
        assert "TASK_002" in result.output
        assert "TODO" in result.output

    def test_not_found(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "nonexistent", "--type", "story"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestStatusAutoDetect:
    def test_detects_epic(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "checkout"])
        assert result.exit_code == 0
        assert "Epic:" in result.output

    def test_detects_story_when_no_epic_match(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        # STORY_002 won't match any epic name
        result = runner.invoke(cli, ["status", "STORY_002", "--type", "story"])
        assert result.exit_code == 0
        assert "Story:" in result.output

    def test_not_found_anywhere(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestStatusWithDoneTask:
    def test_done_task_counted(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        """When a task is DONE, the count reflects it."""
        patch_root(project_with_epic)
        # Mark TASK_001 in STORY_001 as DONE
        task_file = (
            project_with_epic / "work" / "EPIC_001_checkout_resume"
            / "stories" / "STORY_001" / "TASK_001_create_cart_session_table.md"
        )
        content = task_file.read_text()
        task_file.write_text(content.replace('status: "TODO"', 'status: "DONE"'))

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "checkout"])
        assert result.exit_code == 0
        assert "1/2 tasks done" in result.output
