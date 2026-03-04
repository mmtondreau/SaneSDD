"""Approval management for SaneSDD artifacts."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import frontmatter
import yaml

from ssdd.epic_manager import EpicManager
from ssdd.state import StateManager


class ApprovalManager:
    """Manages approval state for SaneSDD artifacts.

    Approval is recorded as an ``approved: "YYYY-MM-DD"`` field in
    YAML frontmatter (for markdown files) or as a top-level key
    (for ``development_plan.yaml``).
    """

    STEPS = ("feature", "design", "stories", "tasks", "plan")

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._state = StateManager(project_root)
        self._epics = EpicManager(project_root)

    # ── Approve operations ────────────────────────────────────────

    def _stamp(self) -> str:
        return date.today().isoformat()

    def _approve_md(self, path: Path) -> dict[str, Any]:
        """Set the ``approved`` field on a markdown file with frontmatter."""
        doc = self._state.load(path)
        doc.metadata["approved"] = self._stamp()
        doc.metadata["updated"] = self._stamp()
        self._state.save(doc)
        return {"path": str(path), "approved": doc.metadata["approved"]}

    def approve_feature(self, name: str) -> dict[str, Any]:
        """Approve a feature spec."""
        feat_dir = self._state.find_feature_dir(name)
        if not feat_dir:
            return {"error": f"Feature '{name}' not found"}
        feature_path = feat_dir / "feature.md"
        if not feature_path.exists():
            return {"error": f"feature.md not found in {feat_dir}"}
        result = self._approve_md(feature_path)
        return {"step": "feature", "approved": [result]}

    def approve_design(self, epic_name: str) -> dict[str, Any]:
        """Approve the high-level design for an epic."""
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        hld_path = epic_dir / "high_level_design.md"
        if not hld_path.exists():
            return {"error": f"high_level_design.md not found in {epic_dir}"}
        result = self._approve_md(hld_path)
        return {"step": "design", "approved": [result]}

    def approve_stories(self, epic_name: str) -> dict[str, Any]:
        """Approve all work stories in an epic."""
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        stories_dir = epic_dir / "stories"
        if not stories_dir.exists():
            return {"error": f"No stories directory in {epic_dir}"}
        results: list[dict[str, Any]] = []
        for story_dir in sorted(stories_dir.iterdir()):
            if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                continue
            story_file = story_dir / "story.md"
            if story_file.exists():
                results.append(self._approve_md(story_file))
        if not results:
            return {"error": "No stories found to approve"}
        return {"step": "stories", "approved": results}

    def approve_tasks(self, epic_name: str) -> dict[str, Any]:
        """Approve all tasks in an epic."""
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        stories_dir = epic_dir / "stories"
        if not stories_dir.exists():
            return {"error": f"No stories directory in {epic_dir}"}
        results: list[dict[str, Any]] = []
        for story_dir in sorted(stories_dir.iterdir()):
            if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                continue
            for task_file in sorted(story_dir.glob("TASK_*.md")):
                results.append(self._approve_md(task_file))
        if not results:
            return {"error": "No tasks found to approve"}
        return {"step": "tasks", "approved": results}

    def approve_plan(self, epic_name: str) -> dict[str, Any]:
        """Approve the development plan for an epic."""
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        plan_path = epic_dir / "development_plan.yaml"
        if not plan_path.exists():
            return {"error": f"development_plan.yaml not found in {epic_dir}"}
        data = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        data["approved"] = self._stamp()
        plan_path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        return {
            "step": "plan",
            "approved": [{"path": str(plan_path), "approved": data["approved"]}],
        }

    def approve(self, step: str, name: str) -> dict[str, Any]:
        """Dispatch to the correct approve method by step name."""
        method = getattr(self, f"approve_{step}", None)
        if not method:
            return {"error": f"Unknown step '{step}'"}
        return method(name)

    # ── Check operations ──────────────────────────────────────────

    def _check_md_approved(self, path: Path) -> bool:
        """Check if a markdown file has the ``approved`` field set."""
        post = frontmatter.load(str(path))
        return bool(post.metadata.get("approved"))

    def check_approval(self, step: str, name: str) -> dict[str, Any]:
        """Check whether artifacts from a prior step are approved.

        Returns ``{"approved": True}`` or
        ``{"approved": False, "unapproved": [...]}``.
        """
        method = getattr(self, f"_check_{step}", None)
        if not method:
            return {"error": f"Unknown step '{step}'"}
        return method(name)

    def _check_feature(self, name: str) -> dict[str, Any]:
        feat_dir = self._state.find_feature_dir(name)
        if not feat_dir:
            return {"error": f"Feature '{name}' not found"}
        feature_path = feat_dir / "feature.md"
        if not feature_path.exists():
            return {"error": f"feature.md not found in {feat_dir}"}
        if self._check_md_approved(feature_path):
            return {"approved": True}
        return {"approved": False, "unapproved": [str(feature_path)]}

    def _check_design(self, epic_name: str) -> dict[str, Any]:
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        hld_path = epic_dir / "high_level_design.md"
        if not hld_path.exists():
            return {"error": f"high_level_design.md not found in {epic_dir}"}
        if self._check_md_approved(hld_path):
            return {"approved": True}
        return {"approved": False, "unapproved": [str(hld_path)]}

    def _check_stories(self, epic_name: str) -> dict[str, Any]:
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        stories_dir = epic_dir / "stories"
        if not stories_dir.exists():
            return {"error": f"No stories directory in {epic_dir}"}
        unapproved: list[str] = []
        for story_dir in sorted(stories_dir.iterdir()):
            if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                continue
            story_file = story_dir / "story.md"
            if story_file.exists() and not self._check_md_approved(story_file):
                unapproved.append(str(story_file))
        if unapproved:
            return {"approved": False, "unapproved": unapproved}
        return {"approved": True}

    def _check_tasks(self, epic_name: str) -> dict[str, Any]:
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        stories_dir = epic_dir / "stories"
        if not stories_dir.exists():
            return {"error": f"No stories directory in {epic_dir}"}
        unapproved: list[str] = []
        for story_dir in sorted(stories_dir.iterdir()):
            if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                continue
            for task_file in sorted(story_dir.glob("TASK_*.md")):
                if not self._check_md_approved(task_file):
                    unapproved.append(str(task_file))
        if unapproved:
            return {"approved": False, "unapproved": unapproved}
        return {"approved": True}

    def _check_plan(self, epic_name: str) -> dict[str, Any]:
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            return {"error": f"Epic '{epic_name}' not found"}
        plan_path = epic_dir / "development_plan.yaml"
        if not plan_path.exists():
            return {"error": f"development_plan.yaml not found in {epic_dir}"}
        data = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        if data.get("approved"):
            return {"approved": True}
        return {"approved": False, "unapproved": [str(plan_path)]}
