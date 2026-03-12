"""Tests for files-to-review generation."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

import ssdd.util_cli as _util_mod
from click.testing import CliRunner
from ssdd.files_to_review import FilesToReviewGenerator
from ssdd.util_cli import cli


@pytest.fixture
def patch_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provides a context that patches find_project_root."""
    def _set(root: Path) -> None:
        monkeypatch.setattr(_util_mod, "find_project_root", lambda: root)
    yield _set  # type: ignore[misc]


# ── Unit tests ───────────────────────────────────────────────────


class TestFeatureStep:
    def test_lists_feature_files(self, project_with_feature: Path) -> None:
        gen = FilesToReviewGenerator(project_with_feature)
        output = gen.generate("feature", "checkout")
        assert "**Files to review:**" in output
        assert "[feature.md]" in output
        assert "/ssdd-approve" in output
        assert "/ssdd-design" in output

    def test_not_found(self, tmp_project: Path) -> None:
        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("feature", "nonexistent")
        assert "not found" in output


class TestDesignStep:
    def test_lists_design_files(self, project_with_epic: Path) -> None:
        # Create design files
        design_dir = project_with_epic / ".ssdd" / "design"
        (design_dir / "design.md").write_text("# Design\n")
        domain_dir = design_dir / "DOMAIN_001_checkout"
        domain_dir.mkdir()
        (domain_dir / "domain.md").write_text("# Domain\n")
        (domain_dir / "COMP_cart.md").write_text("# Cart\n")

        # Create HLD
        epic_dir = project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume"
        (epic_dir / "high_level_design.md").write_text("# HLD\n")

        gen = FilesToReviewGenerator(project_with_epic)
        output = gen.generate("design", "checkout")
        assert "Epic:" in output
        assert "[high_level_design.md]" in output
        assert "System architecture:" in output
        assert "[design.md]" in output
        assert "Domains:" in output
        assert "[domain.md]" in output
        assert "Components:" in output
        assert "[COMP_cart.md]" in output
        assert "/ssdd-stories" in output

    def test_not_found(self, tmp_project: Path) -> None:
        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("design", "nonexistent")
        assert "not found" in output


class TestStoriesStep:
    def test_lists_story_files(self, project_with_epic: Path) -> None:
        gen = FilesToReviewGenerator(project_with_epic)
        output = gen.generate("stories", "checkout")
        assert "Stories:" in output
        assert "[story.md]" in output
        assert "/ssdd-tasks" in output
        # Should suggest directory-level approval
        assert "/ssdd-approve" in output

    def test_not_found(self, tmp_project: Path) -> None:
        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("stories", "nonexistent")
        assert "not found" in output


class TestTasksStep:
    def test_lists_task_files(self, project_with_epic: Path) -> None:
        gen = FilesToReviewGenerator(project_with_epic)
        output = gen.generate("tasks", "checkout")
        assert "STORY_001 tasks:" in output
        assert "STORY_002 tasks:" in output
        assert "[TASK_" in output
        assert "/ssdd-plan" in output

    def test_not_found(self, tmp_project: Path) -> None:
        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("tasks", "nonexistent")
        assert "not found" in output


class TestPlanStep:
    def test_lists_plan_file(self, project_with_epic: Path) -> None:
        gen = FilesToReviewGenerator(project_with_epic)
        output = gen.generate("plan", "checkout")
        assert "[development_plan.yaml]" in output
        assert "/ssdd-implement" in output

    def test_not_found(self, tmp_project: Path) -> None:
        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("plan", "nonexistent")
        assert "not found" in output


class TestImplementStep:
    def test_lists_story_and_tasks(self, project_with_epic: Path) -> None:
        gen = FilesToReviewGenerator(project_with_epic)
        output = gen.generate("implement", "checkout")
        assert "Updated stories and tasks:" in output
        assert "[story.md]" in output
        assert "[TASK_" in output
        # Fixture work story has status DONE
        assert "complete" in output.lower()

    def test_with_promoted_stories(self, project_with_epic: Path) -> None:
        promoted = str(
            project_with_epic / ".ssdd" / "specs"
            / "FEAT_001_checkout_resume" / "stories" / "STORY_001_save_cart.md"
        )
        gen = FilesToReviewGenerator(project_with_epic)
        output = gen.generate("implement", "checkout", [promoted])
        assert "Promoted spec stories:" in output

    def test_done_story(self, project_with_epic: Path) -> None:
        # Mark story as DONE
        story_md = (
            project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume"
            / "stories" / "STORY_001" / "story.md"
        )
        content = story_md.read_text()
        content = content.replace('status: "TODO"', 'status: "DONE"')
        story_md.write_text(content)

        gen = FilesToReviewGenerator(project_with_epic)
        output = gen.generate("implement", "checkout")
        assert "complete" in output.lower()
        assert "/ssdd-merge" in output


class TestInitStep:
    def test_lists_design_files(self, tmp_project: Path) -> None:
        design_dir = tmp_project / ".ssdd" / "design"
        (design_dir / "design.md").write_text("# Design\n")
        domain_dir = design_dir / "DOMAIN_001_core"
        domain_dir.mkdir()
        (domain_dir / "domain.md").write_text("# Core\n")
        (domain_dir / "COMP_api.md").write_text("# API\n")

        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("init")
        assert "System architecture:" in output
        assert "Domains:" in output
        assert "Components:" in output
        assert "/ssdd-feature" in output

    def test_empty_design(self, tmp_project: Path) -> None:
        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("init")
        assert output == ""


class TestUnknownStep:
    def test_unknown_step(self, tmp_project: Path) -> None:
        gen = FilesToReviewGenerator(tmp_project)
        output = gen.generate("bogus")
        assert "Unknown step" in output


# ── CLI integration tests ────────────────────────────────────────


class TestFilesToReviewCLI:
    def test_feature_step(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["files-to-review", "feature", "checkout"])
        assert result.exit_code == 0
        assert "**Files to review:**" in result.output

    def test_stories_step(self, project_with_epic: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_epic)
        runner = CliRunner()
        result = runner.invoke(cli, ["files-to-review", "stories", "checkout"])
        assert result.exit_code == 0
        assert "Stories:" in result.output

    def test_init_no_name(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["files-to-review", "init"])
        assert result.exit_code == 0

    def test_invalid_step(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["files-to-review", "bogus"])
        assert result.exit_code != 0
