"""Parses development_plan.yaml into typed execution plan."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from sdd.state import StateManager
from sdd.workstream import WorkstreamManager


@dataclass(frozen=True)
class TaskRef:
    """A reference to a task within the execution plan."""
    task_id: str
    task_path: Path
    order: int


@dataclass(frozen=True)
class StoryRef:
    """A reference to a story within the execution plan."""
    story_id: str
    story_path: Path
    tasks: tuple[TaskRef, ...]
    order: int


@dataclass(frozen=True)
class DevelopmentPlan:
    """Parsed development_plan.yaml for a feature."""
    feature_name: str
    stories: tuple[StoryRef, ...]


class PlanParser:
    """Parses development_plan.yaml into typed execution plan.

    Expected YAML structure:

        feature: FEAT_001_checkout_resume
        stories:
          - story_id: STORY_001
            order: 1
            tasks:
              - task_id: TASK_001
                order: 1
              - task_id: TASK_002
                order: 2
          - story_id: STORY_002
            order: 2
            tasks:
              - task_id: TASK_001
                order: 1
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._state = StateManager(project_root)
        self._ws = WorkstreamManager(project_root)

    def load(self, feature_name: str) -> DevelopmentPlan:
        ws_feat_dir = self._ws.find_active(feature_name)
        if not ws_feat_dir:
            raise FileNotFoundError(
                f"No active workstream for '{feature_name}'. Run `sdd design` first."
            )

        plan_path = ws_feat_dir / "development_plan.yaml"
        if not plan_path.exists():
            raise FileNotFoundError(
                f"No development plan at {plan_path}. Run `sdd plan` first."
            )

        with open(plan_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        feature_slug = raw.get("feature", feature_name)
        feat_dir = self._state.find_feature_dir(feature_slug)

        parsed_stories: list[StoryRef] = []
        for story_raw in sorted(raw.get("stories", []), key=lambda s: s["order"]):
            sid = story_raw["story_id"]
            story_path = self._resolve_story_path(feat_dir, sid)

            parsed_tasks: list[TaskRef] = []
            for task_raw in sorted(story_raw.get("tasks", []), key=lambda t: t["order"]):
                tid = task_raw["task_id"]
                # Find the actual task file (may have a slug suffix)
                task_path = self._resolve_task_path(ws_feat_dir, sid, tid)
                parsed_tasks.append(TaskRef(
                    task_id=tid,
                    task_path=task_path,
                    order=task_raw["order"],
                ))

            parsed_stories.append(StoryRef(
                story_id=sid,
                story_path=story_path,
                tasks=tuple(parsed_tasks),
                order=story_raw["order"],
            ))

        return DevelopmentPlan(
            feature_name=feature_slug,
            stories=tuple(parsed_stories),
        )

    def _resolve_story_path(self, feat_dir: Path | None, story_id: str) -> Path:
        if not feat_dir:
            raise FileNotFoundError("Feature directory not found")
        stories_dir = feat_dir / "stories"
        for f in stories_dir.glob(f"{story_id}*.md"):
            return f
        raise FileNotFoundError(f"Story {story_id} not found in {stories_dir}")

    def _resolve_task_path(self, ws_feat_dir: Path, story_id: str, task_id: str) -> Path:
        task_dir = ws_feat_dir / "stories" / story_id
        if not task_dir.exists():
            # Try with slug suffix on story dir
            parent = ws_feat_dir / "stories"
            for d in parent.iterdir():
                if d.is_dir() and d.name.startswith(story_id):
                    task_dir = d
                    break

        for f in task_dir.glob(f"{task_id}*.md"):
            return f
        # Fall back to exact path
        return task_dir / f"{task_id}.md"
