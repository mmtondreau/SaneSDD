"""Tests for ssdd-util CLI commands."""

from __future__ import annotations

import json
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from click.testing import CliRunner

import ssdd.util_cli as _util_mod
from ssdd.util_cli import cli

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
        assert (tmp_path / ".ssdd" / "specs").is_dir()
        assert (tmp_path / ".ssdd" / "work").is_dir()
        assert (tmp_path / ".ssdd" / "design").is_dir()
        assert (tmp_path / ".ssdd" / "INDEX.md").exists()

    def test_init_creates_index(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(cli, ["init", "--path", str(tmp_path)])
        index = (tmp_path / ".ssdd" / "INDEX.md").read_text()
        assert "# SaneSDD Project Index" in index

    def test_init_idempotent(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(cli, ["init", "--path", str(tmp_path)])
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "already initialized" in result.output

    def test_init_partial_existing(self, tmp_path: Path) -> None:
        (tmp_path / ".ssdd" / "specs").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / ".ssdd" / "work").is_dir()
        assert (tmp_path / ".ssdd" / "design").is_dir()


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
        feat_dir = project_with_feature / ".ssdd" / "specs" / "FEAT_001_checkout_resume"
        runner = CliRunner()
        result = runner.invoke(cli, ["next-story-number", str(feat_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, project_with_stories: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_stories)
        feat_dir = project_with_stories / ".ssdd" / "specs" / "FEAT_001_checkout_resume"
        runner = CliRunner()
        result = runner.invoke(cli, ["next-story-number", str(feat_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "3"


class TestNextTaskNumber:
    def test_returns_1_for_empty_dir(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        story_dir = project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume" / "stories" / "STORY_003"
        story_dir.mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-task-number", str(story_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        story_dir = project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume" / "stories" / "STORY_001"
        runner = CliRunner()
        result = runner.invoke(cli, ["next-task-number", str(story_dir)])
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


class TestRegenerateIndex:
    def test_regenerates_index(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["regenerate-index"])
        assert result.exit_code == 0
        assert "regenerated" in result.output
        assert (project_with_feature / ".ssdd" / "INDEX.md").exists()


class TestPlanJson:
    def test_outputs_valid_json(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["plan-json", "checkout"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "epic" in data
        assert "stories" in data
        assert len(data["stories"]) > 0

    def test_stories_have_tasks(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
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

    def test_errors_when_no_epic(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["plan-json", "checkout"])
        assert result.exit_code != 0


# ── New CLI command tests ─────────────────────────────────────────


class TestNextThemeNumber:
    def test_returns_1_for_empty_project(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-theme-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        (tmp_project / ".ssdd" / "specs" / "THEME_001_ecommerce").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-theme-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "2"


class TestFindTheme:
    def test_finds_by_substring(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        (tmp_project / ".ssdd" / "specs" / "THEME_001_ecommerce").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-theme", "ecommerce"])
        assert result.exit_code == 0
        assert "THEME_001_ecommerce" in result.output

    def test_errors_when_not_found(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-theme", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestNextFeatureNumberInTheme:
    def test_returns_1_for_empty_theme(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        theme_dir = tmp_project / ".ssdd" / "specs" / "THEME_001_ecommerce"
        theme_dir.mkdir(parents=True)
        (theme_dir / "features").mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["next-feature-number-in-theme", str(theme_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        theme_dir = tmp_project / ".ssdd" / "specs" / "THEME_001_ecommerce"
        (theme_dir / "features" / "FEAT_001_checkout").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-feature-number-in-theme", str(theme_dir)])
        assert result.exit_code == 0
        assert result.output.strip() == "2"


class TestNextEpicNumber:
    def test_returns_1_for_empty_project(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-epic-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        (tmp_project / ".ssdd" / "work" / "EPIC_001_test").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-epic-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "2"


class TestFindEpic:
    def test_finds_by_substring(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        (tmp_project / ".ssdd" / "work" / "EPIC_001_checkout").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-epic", "checkout"])
        assert result.exit_code == 0
        assert "EPIC_001_checkout" in result.output

    def test_errors_when_not_found(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-epic", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestCreateEpic:
    def test_creates_epic(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["create-epic", "checkout"])
        assert result.exit_code == 0
        assert "EPIC_001_checkout" in result.output
        epic_dir = tmp_project / ".ssdd" / "work" / "EPIC_001_checkout"
        assert epic_dir.is_dir()
        assert (epic_dir / "stories").is_dir()

    def test_increments_epic_number(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        runner.invoke(cli, ["create-epic", "first"])
        result = runner.invoke(cli, ["create-epic", "second"])
        assert result.exit_code == 0
        assert "EPIC_002_second" in result.output


class TestNextDomainNumber:
    def test_returns_1_for_empty_design(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-domain-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_returns_next_after_existing(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        (tmp_project / ".ssdd" / "design" / "DOMAIN_001_commerce").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["next-domain-number"])
        assert result.exit_code == 0
        assert result.output.strip() == "2"


class TestFindDomain:
    def test_finds_by_substring(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        (tmp_project / ".ssdd" / "design" / "DOMAIN_001_commerce").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-domain", "commerce"])
        assert result.exit_code == 0
        assert "DOMAIN_001_commerce" in result.output

    def test_errors_when_not_found(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["find-domain", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestPromoteStory:
    def test_promotes_story(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        # Set up epic with work story
        epic_dir = tmp_project / ".ssdd" / "work" / "EPIC_001_checkout"
        epic_dir.mkdir(parents=True)
        (epic_dir / "stories").mkdir()
        shutil.copy(FIXTURES_DIR / "sample_epic.md", epic_dir / "epic.md")

        story_dir = epic_dir / "stories" / "STORY_001"
        story_dir.mkdir()
        shutil.copy(FIXTURES_DIR / "sample_work_story.md", story_dir / "story.md")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "promote-story", str(story_dir / "story.md"),
            "--epic", str(epic_dir),
        ])
        assert result.exit_code == 0
        # Spec story should have been created
        specs_dir = tmp_project / ".ssdd" / "specs"
        theme_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
        assert len(theme_dirs) > 0
