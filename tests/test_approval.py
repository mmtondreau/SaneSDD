"""Tests for approval management."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import frontmatter
import pytest
import yaml
from click.testing import CliRunner

import ssdd.util_cli as _util_mod
from ssdd.approval_manager import ApprovalManager
from ssdd.util_cli import cli


@pytest.fixture
def patch_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provides a context that patches find_project_root."""
    def _set(root: Path) -> None:
        monkeypatch.setattr(_util_mod, "find_project_root", lambda: root)
    yield _set  # type: ignore[misc]


# ── ApprovalManager unit tests ───────────────────────────────────


class TestApproveFeature:
    def test_approves_feature(self, project_with_feature: Path) -> None:
        mgr = ApprovalManager(project_with_feature)
        result = mgr.approve_feature("checkout")
        assert result["step"] == "feature"
        assert len(result["approved"]) == 1
        # Verify frontmatter was written
        post = frontmatter.load(str(result["approved"][0]["path"]))
        assert post.metadata["approved"]

    def test_idempotent(self, project_with_feature: Path) -> None:
        mgr = ApprovalManager(project_with_feature)
        mgr.approve_feature("checkout")
        result = mgr.approve_feature("checkout")
        assert result["step"] == "feature"

    def test_not_found(self, tmp_project: Path) -> None:
        mgr = ApprovalManager(tmp_project)
        result = mgr.approve_feature("nonexistent")
        assert "error" in result


class TestApproveDesign:
    def test_approves_hld(self, project_with_epic: Path) -> None:
        # Create an HLD file
        epic_dir = project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume"
        hld = epic_dir / "high_level_design.md"
        hld.write_text("# High-Level Design\n\nSome design content.\n")
        mgr = ApprovalManager(project_with_epic)
        result = mgr.approve_design("checkout")
        assert result["step"] == "design"
        # File should now have frontmatter
        post = frontmatter.load(str(hld))
        assert post.metadata["approved"]

    def test_hld_with_existing_frontmatter(self, project_with_epic: Path) -> None:
        epic_dir = project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume"
        hld = epic_dir / "high_level_design.md"
        hld.write_text(
            '---\nepic: "EPIC_001"\ntitle: "Checkout Resume"\n---\n\n# Design\n'
        )
        mgr = ApprovalManager(project_with_epic)
        result = mgr.approve_design("checkout")
        assert result["step"] == "design"
        post = frontmatter.load(str(hld))
        assert post.metadata["approved"]
        assert post.metadata["epic"] == "EPIC_001"

    def test_not_found(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        result = mgr.approve_design("checkout")
        assert "error" in result
        assert "high_level_design.md not found" in result["error"]


class TestApproveStories:
    def test_approves_all_stories(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        result = mgr.approve_stories("checkout")
        assert result["step"] == "stories"
        assert len(result["approved"]) == 2

    def test_not_found(self, tmp_project: Path) -> None:
        mgr = ApprovalManager(tmp_project)
        result = mgr.approve_stories("nonexistent")
        assert "error" in result


class TestApproveTasks:
    def test_approves_all_tasks(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        result = mgr.approve_tasks("checkout")
        assert result["step"] == "tasks"
        # 2 tasks in STORY_001 + 1 task in STORY_002
        assert len(result["approved"]) == 3

    def test_not_found(self, tmp_project: Path) -> None:
        mgr = ApprovalManager(tmp_project)
        result = mgr.approve_tasks("nonexistent")
        assert "error" in result


class TestApprovePlan:
    def test_approves_plan(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        result = mgr.approve_plan("checkout")
        assert result["step"] == "plan"
        # Verify YAML was updated
        plan_path = (
            project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume"
            / "development_plan.yaml"
        )
        data = yaml.safe_load(plan_path.read_text())
        assert data["approved"]
        # Other keys preserved
        assert data["epic"] == "EPIC_001_checkout_resume"
        assert len(data["stories"]) == 2

    def test_not_found(self, tmp_project: Path) -> None:
        mgr = ApprovalManager(tmp_project)
        result = mgr.approve_plan("nonexistent")
        assert "error" in result


# ── Check approval tests ─────────────────────────────────────────


class TestCheckApproval:
    def test_feature_not_approved(self, project_with_feature: Path) -> None:
        mgr = ApprovalManager(project_with_feature)
        result = mgr.check_approval("feature", "checkout")
        assert result["approved"] is False
        assert len(result["unapproved"]) == 1

    def test_feature_approved(self, project_with_feature: Path) -> None:
        mgr = ApprovalManager(project_with_feature)
        mgr.approve_feature("checkout")
        result = mgr.check_approval("feature", "checkout")
        assert result["approved"] is True

    def test_stories_partial(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        # Approve only one story manually
        story_file = (
            project_with_epic / ".ssdd" / "work" / "EPIC_001_checkout_resume"
            / "stories" / "STORY_001" / "story.md"
        )
        post = frontmatter.load(str(story_file))
        post.metadata["approved"] = "2026-03-01"
        with open(story_file, "w") as f:
            f.write(frontmatter.dumps(post))
        result = mgr.check_approval("stories", "checkout")
        assert result["approved"] is False
        assert len(result["unapproved"]) == 1  # STORY_002 still unapproved

    def test_tasks_not_approved(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        result = mgr.check_approval("tasks", "checkout")
        assert result["approved"] is False
        assert len(result["unapproved"]) == 3

    def test_plan_not_approved(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        result = mgr.check_approval("plan", "checkout")
        assert result["approved"] is False

    def test_plan_approved(self, project_with_epic: Path) -> None:
        mgr = ApprovalManager(project_with_epic)
        mgr.approve_plan("checkout")
        result = mgr.check_approval("plan", "checkout")
        assert result["approved"] is True

    def test_unknown_step(self, tmp_project: Path) -> None:
        mgr = ApprovalManager(tmp_project)
        result = mgr.check_approval("bogus", "anything")
        assert "error" in result


# ── CLI integration tests ────────────────────────────────────────


class TestApproveCLI:
    def test_approve_feature(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["approve", "feature", "checkout"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["step"] == "feature"

    def test_approve_not_found(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["approve", "feature", "nonexistent"])
        assert result.exit_code != 0

    def test_approve_invalid_step(self, tmp_project: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(tmp_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["approve", "bogus", "anything"])
        assert result.exit_code != 0


class TestCheckApprovalCLI:
    def test_check_not_approved(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        result = runner.invoke(cli, ["check-approval", "feature", "checkout"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["approved"] is False

    def test_check_after_approve(self, project_with_feature: Path, patch_root) -> None:  # type: ignore[no-untyped-def]
        patch_root(project_with_feature)
        runner = CliRunner()
        runner.invoke(cli, ["approve", "feature", "checkout"])
        result = runner.invoke(cli, ["check-approval", "feature", "checkout"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["approved"] is True
