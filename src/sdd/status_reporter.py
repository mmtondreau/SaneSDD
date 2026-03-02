"""Status reporting for epics and stories."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import frontmatter


@dataclass
class TaskStatus:
    """Status info for a single task."""
    id: str
    title: str
    status: str


@dataclass
class StoryStatus:
    """Status info for a single story with its tasks."""
    id: str
    title: str
    status: str
    tasks: list[TaskStatus] = field(default_factory=list)


@dataclass
class EpicStatus:
    """Status info for an epic with its stories."""
    id: str
    title: str
    status: str
    path: Path
    stories: list[StoryStatus] = field(default_factory=list)


def _load_meta(path: Path) -> dict[str, Any]:
    """Load YAML frontmatter from a markdown file."""
    post = frontmatter.load(str(path))
    return dict(post.metadata)


class StatusReporter:
    """Reports status of epics, stories, and tasks."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._work_dir = project_root / "work"

    def _list_epic_dirs(self) -> list[Path]:
        """List all EPIC_* directories under work/."""
        if not self._work_dir.exists():
            return []
        return sorted(
            d for d in self._work_dir.iterdir()
            if d.is_dir() and re.match(r"EPIC_\d{3}_", d.name)
        )

    def _find_epic(self, name: str) -> Path | None:
        """Find an epic directory by exact name or substring match."""
        for d in self._list_epic_dirs():
            if d.name == name or name in d.name:
                return d
        return None

    def _find_story_dir(self, name: str) -> tuple[Path, Path] | None:
        """Find a work story directory by name/ID/substring.

        Returns (epic_dir, story_dir) or None.
        """
        for epic_dir in self._list_epic_dirs():
            stories_dir = epic_dir / "stories"
            if not stories_dir.exists():
                continue
            for story_dir in sorted(stories_dir.iterdir()):
                if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                    continue
                if story_dir.name == name or name in story_dir.name:
                    return (epic_dir, story_dir)
        return None

    def _get_tasks_for_story(self, story_dir: Path) -> list[TaskStatus]:
        """Load all tasks in a story directory."""
        tasks: list[TaskStatus] = []
        for task_file in sorted(story_dir.glob("TASK_*.md")):
            meta = _load_meta(task_file)
            tasks.append(TaskStatus(
                id=meta.get("id", task_file.stem),
                title=meta.get("title", ""),
                status=meta.get("status", "TODO"),
            ))
        return tasks

    def _get_stories_for_epic(self, epic_dir: Path) -> list[StoryStatus]:
        """Load all stories (with tasks) for an epic."""
        stories: list[StoryStatus] = []
        stories_dir = epic_dir / "stories"
        if not stories_dir.exists():
            return stories
        for story_dir in sorted(stories_dir.iterdir()):
            if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                continue
            story_file = story_dir / "story.md"
            if not story_file.exists():
                continue
            meta = _load_meta(story_file)
            tasks = self._get_tasks_for_story(story_dir)
            stories.append(StoryStatus(
                id=meta.get("id", story_dir.name),
                title=meta.get("title", ""),
                status=meta.get("status", "TODO"),
                tasks=tasks,
            ))
        return stories

    def epic_status(self, name: str) -> EpicStatus | None:
        """Get status for a single epic by name/substring."""
        epic_dir = self._find_epic(name)
        if not epic_dir:
            return None
        epic_file = epic_dir / "epic.md"
        if not epic_file.exists():
            return None
        meta = _load_meta(epic_file)
        stories = self._get_stories_for_epic(epic_dir)
        return EpicStatus(
            id=meta.get("id", epic_dir.name),
            title=meta.get("title", ""),
            status=meta.get("status", "TODO"),
            path=epic_dir,
            stories=stories,
        )

    def all_epics_status(self) -> list[EpicStatus]:
        """Get status for all epics."""
        results: list[EpicStatus] = []
        for epic_dir in self._list_epic_dirs():
            epic_file = epic_dir / "epic.md"
            if not epic_file.exists():
                continue
            meta = _load_meta(epic_file)
            stories = self._get_stories_for_epic(epic_dir)
            results.append(EpicStatus(
                id=meta.get("id", epic_dir.name),
                title=meta.get("title", ""),
                status=meta.get("status", "TODO"),
                path=epic_dir,
                stories=stories,
            ))
        return results

    def story_status(self, name: str) -> tuple[EpicStatus | None, StoryStatus] | None:
        """Get status for a single story by name/substring.

        Returns (parent_epic_status_summary, story_status) or None.
        """
        result = self._find_story_dir(name)
        if not result:
            return None
        epic_dir, story_dir = result
        story_file = story_dir / "story.md"
        if not story_file.exists():
            return None
        meta = _load_meta(story_file)
        tasks = self._get_tasks_for_story(story_dir)
        story = StoryStatus(
            id=meta.get("id", story_dir.name),
            title=meta.get("title", ""),
            status=meta.get("status", "TODO"),
            tasks=tasks,
        )
        # Minimal epic info for context
        epic_file = epic_dir / "epic.md"
        epic_info = None
        if epic_file.exists():
            epic_meta = _load_meta(epic_file)
            epic_info = EpicStatus(
                id=epic_meta.get("id", epic_dir.name),
                title=epic_meta.get("title", ""),
                status=epic_meta.get("status", "TODO"),
                path=epic_dir,
            )
        return (epic_info, story)


def format_epic_status(epic: EpicStatus) -> str:
    """Format an epic's status as a human-readable string."""
    lines: list[str] = []
    lines.append(f"Epic: {epic.id} — {epic.title}")
    lines.append(f"Status: {epic.status}")
    if not epic.stories:
        lines.append("  (no stories)")
        return "\n".join(lines)
    lines.append(f"Stories ({len(epic.stories)}):")
    for story in epic.stories:
        task_done = sum(1 for t in story.tasks if t.status == "DONE")
        task_total = len(story.tasks)
        task_summary = f" [{task_done}/{task_total} tasks done]" if task_total > 0 else ""
        lines.append(f"  {story.id} — {story.title}: {story.status}{task_summary}")
    return "\n".join(lines)


def format_story_status(
    story: StoryStatus, epic: EpicStatus | None = None
) -> str:
    """Format a story's status as a human-readable string."""
    lines: list[str] = []
    if epic:
        lines.append(f"Epic: {epic.id} — {epic.title}")
    lines.append(f"Story: {story.id} — {story.title}")
    lines.append(f"Status: {story.status}")
    if not story.tasks:
        lines.append("  (no tasks)")
        return "\n".join(lines)
    lines.append(f"Tasks ({len(story.tasks)}):")
    for task in story.tasks:
        lines.append(f"  {task.id} — {task.title}: {task.status}")
    return "\n".join(lines)
