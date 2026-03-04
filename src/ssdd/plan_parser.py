"""Parses development_plan.yaml into typed execution plan."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ssdd.epic_manager import EpicManager


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
    """Parsed development_plan.yaml for an epic."""
    epic_name: str
    stories: tuple[StoryRef, ...]


class PlanParser:
    """Parses development_plan.yaml into typed execution plan.

    Expected YAML structure:

        epic: EPIC_001_checkout_resume
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

    Also supports the legacy 'feature' key for backward compatibility.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._epics = EpicManager(project_root)

    def load(self, epic_name: str) -> DevelopmentPlan:
        epic_dir = self._epics.find_epic(epic_name)
        if not epic_dir:
            raise FileNotFoundError(
                f"No epic found for '{epic_name}'. Run `sdd design` first."
            )

        plan_path = epic_dir / "development_plan.yaml"
        if not plan_path.exists():
            raise FileNotFoundError(
                f"No development plan at {plan_path}. Run `sdd plan` first."
            )

        with open(plan_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        epic_slug = raw.get("epic", raw.get("feature", epic_name))

        parsed_stories: list[StoryRef] = []
        for story_raw in sorted(raw.get("stories", []), key=lambda s: s["order"]):
            sid = story_raw["story_id"]
            story_path = self._resolve_story_path(epic_dir, sid)

            parsed_tasks: list[TaskRef] = []
            for task_raw in sorted(story_raw.get("tasks", []), key=lambda t: t["order"]):
                tid = task_raw["task_id"]
                task_path = self._resolve_task_path(epic_dir, sid, tid)
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
            epic_name=epic_slug,
            stories=tuple(parsed_stories),
        )

    def _resolve_story_path(self, epic_dir: Path, story_id: str) -> Path:
        """Resolve a story path within the epic's stories directory."""
        stories_dir = epic_dir / "stories"
        # Work stories live in STORY_NNN/story.md
        story_dir = stories_dir / story_id
        if story_dir.is_dir():
            story_md = story_dir / "story.md"
            if story_md.exists():
                return story_md
        # Try with slug suffix on story dir
        for d in stories_dir.iterdir():
            if d.is_dir() and d.name.startswith(story_id):
                story_md = d / "story.md"
                if story_md.exists():
                    return story_md
        raise FileNotFoundError(f"Story {story_id} not found in {stories_dir}")

    def _resolve_task_path(self, epic_dir: Path, story_id: str, task_id: str) -> Path:
        task_dir = epic_dir / "stories" / story_id
        if not task_dir.exists():
            parent = epic_dir / "stories"
            for d in parent.iterdir():
                if d.is_dir() and d.name.startswith(story_id):
                    task_dir = d
                    break

        for f in task_dir.glob(f"{task_id}*.md"):
            return f
        return task_dir / f"{task_id}.md"
