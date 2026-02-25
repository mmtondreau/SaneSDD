"""Tests for sdd-util CLI commands."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from click.testing import CliRunner

import sdd.util_cli as _util_mod
from sdd.util_cli import cli


@pytest.fixture
def patch_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provides a context that patches find_project_root.

    Usage: call with a Path in the test, then invoke the CLI.
    """
    _root: Path | None = None

    def _set(root: Path) -> None:
        nonlocal _root
        _root = root
        monkeypatch.setattr(_util_mod, "find_project_root", lambda: root)

    # Expose the setter as an attribute on the fixture value
    yield _set  # type: ignore[misc]


class TestInit:
    def test_init_creates_directories(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "specs").is_dir()
        assert (tmp_path / "work").is_dir()
        assert (tmp_path / "design").is_dir()
        assert (tmp_path / "INDEX.md").exists()

    def test_init_creates_index(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(cli, ["init", "--path", str(tmp_path)])
        index = (tmp_path / "INDEX.md").read_text()
        assert "# SDD Project Index" in index

    def test_init_idempotent(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(cli, ["init", "--path", str(tmp_path)])
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "already initialized" in result.output

    def test_init_partial_existing(self, tmp_path: Path) -> None:
        (tmp_path / "specs").mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "work").is_dir()
        assert (tmp_path / "design").is_dir()


class TestNextFeatureNumber:
    def test_returns_1_for_empty_project(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-feature-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-feature-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "2"


class TestNextStoryNumber:
    def test_returns_1_for_empty_feature(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        feat_dir = project_with_feature / "specs" / "FEAT_001_checkout_resume"
        runner = CliRunner()
        result = runner.invoke(cli, ["next-story-number", str(feat_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, project_with_stories: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_stories)
        feat_dir = project_with_stories / "specs" / "FEAT_001_checkout_resume"
        runner = CliRunner()
        result = runner.invoke(cli, ["next-story-number", str(feat_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "3"


class TestNextTaskNumber:
    def test_returns_1_for_empty_dir(self, project_with_workstream: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_workstream)
        ws_feat = "work" / Path("WS_001") / "FEAT_001_checkout_resume"
        ws_story_dir = project_with_workstream / ws_feat / "stories" / "STORY_003"
        ws_story_dir.mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-task-number", str(ws_story_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, project_with_workstream: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_workstream)
        ws_feat = "work" / Path("WS_001") / "FEAT_001_checkout_resume"
        ws_story_dir = project_with_workstream / ws_feat / "stories" / "STORY_001"
        runner = CliRunner()
        result = runner.invoke(cli, ["next-task-number", str(ws_story_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "3"


class TestFindFeature:
    def test_finds_by_exact_name(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-feature", "FEAT_001_checkout_resume"])
        assert result.exit_code == 0
        assert "FEAT_001_checkout_resume" in result.output

    def test_finds_by_substring(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-feature", "checkout"])
        assert result.exit_code == 0
        assert "FEAT_001_checkout_resume" in result.output

    def test_errors_when_not_found(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-feature", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestFindWorkstream:
    def test_finds_active_workstream(self, project_with_workstream: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_workstream)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-workstream", "checkout"])
        assert result.exit_code == 0
        assert "WS_001" in result.output
        assert "FEAT_001_checkout_resume" in result.output

    def test_errors_when_no_workstream(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-workstream", "checkout"])
        assert result.exit_code != 0
        assert "No active workstream" in result.output


class TestCreateWorkstream:
    def test_creates_workstream(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["create-workstream", "FEAT_001_test"])
        assert result.exit_code == 0
        assert "WS_001" in result.output
        ws_dir = tmp_project / "work" / "WS_001" / "FEAT_001_test"
        assert ws_dir.is_dir()
        assert (ws_dir / "stories").is_dir()

    def test_increments_workstream_number(self, project_with_workstream: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_workstream)
        runner = CliRunner()
        result = runner.invoke(cli, ["create-workstream", "FEAT_002_test"])
        assert result.exit_code == 0
        assert "WS_002" in result.output


class TestRegenerateIndex:
    def test_regenerates_index(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["regenerate-index"])
        assert result.exit_code == 0
        assert "regenerated" in result.output
        assert (project_with_feature / "INDEX.md").exists()


class TestPlanJson:
    def test_outputs_valid_json(self, project_with_workstream: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_workstream)
        runner = CliRunner()
        result = runner.invoke(cli, ["plan-json", "checkout"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "feature" in data
        assert "stories" in data
        assert len(data["stories"]) > 0

    def test_stories_have_tasks(self, project_with_workstream: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_workstream)
        runner = CliRunner()
        result = runner.invoke(cli, ["plan-json", "checkout"])
        data = json.loads(result.output)
        for story in data["stories"]:
            assert "story_id" in story
            assert "tasks" in story
            assert len(story["tasks"]) > 0
            for task in story["tasks"]:
                assert "task_id" in task
                assert "task_path" in task

    def test_errors_when_no_workstream(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["plan-json", "checkout"])
        assert result.exit_code != 0
