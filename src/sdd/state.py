"""YAML frontmatter state management for SDD artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

import frontmatter


class Status(Enum):
    """Valid statuses for any SDD artifact."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


@dataclass
class AcEntry:
    """A single acceptance criterion within a story."""
    id: str
    description: str
    status: Status

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "description": self.description, "status": self.status.value}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AcEntry:
        return cls(
            id=d["id"],
            description=d["description"],
            status=Status(d.get("status", "TODO")),
        )


@dataclass
class Document:
    """A parsed markdown file with YAML frontmatter."""
    path: Path
    metadata: dict[str, Any]
    content: str

    @property
    def id(self) -> str:
        return str(self.metadata.get("id", ""))

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", ""))

    @property
    def status(self) -> Status:
        return Status(self.metadata.get("status", "TODO"))

    @status.setter
    def status(self, value: Status) -> None:
        self.metadata["status"] = value.value
        self.metadata["updated"] = date.today().isoformat()

    @property
    def depends_on(self) -> list[str]:
        return list(self.metadata.get("depends_on", []))

    @property
    def acceptance_criteria(self) -> list[AcEntry]:
        raw = self.metadata.get("acceptance_criteria", [])
        return [AcEntry.from_dict(ac) for ac in raw]

    @acceptance_criteria.setter
    def acceptance_criteria(self, entries: list[AcEntry]) -> None:
        self.metadata["acceptance_criteria"] = [e.to_dict() for e in entries]
        self.metadata["updated"] = date.today().isoformat()

    @property
    def ac_mapping(self) -> list[str]:
        return list(self.metadata.get("ac_mapping", []))

    def all_acs_done(self) -> bool:
        acs = self.acceptance_criteria
        return len(acs) > 0 and all(ac.status == Status.DONE for ac in acs)


class StateManager:
    """Reads and writes YAML-frontmatter markdown files."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root

    @property
    def specs_dir(self) -> Path:
        return self._root / "specs"

    @property
    def work_dir(self) -> Path:
        return self._root / "work"

    @property
    def design_dir(self) -> Path:
        return self._root / "design"

    # ── Load / Save ──────────────────────────────────────────────

    def load(self, path: Path) -> Document:
        """Load a markdown file with YAML frontmatter."""
        post = frontmatter.load(str(path))
        return Document(
            path=path,
            metadata=dict(post.metadata),
            content=post.content,
        )

    def save(self, doc: Document) -> None:
        """Write a Document back to disk."""
        post = frontmatter.Post(doc.content, **doc.metadata)
        doc.path.parent.mkdir(parents=True, exist_ok=True)
        with open(doc.path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def transition(self, path: Path, new_status: Status) -> Document:
        """Load, update status, save, return."""
        doc = self.load(path)
        doc.status = new_status
        self.save(doc)
        return doc

    # ── Feature operations ───────────────────────────────────────

    def find_feature_dir(self, feature_name: str) -> Path | None:
        """Find a feature directory by exact name or substring match."""
        if not self.specs_dir.exists():
            return None
        for d in sorted(self.specs_dir.iterdir()):
            if d.is_dir() and (d.name == feature_name or feature_name in d.name):
                return d
        return None

    def read_feature(self, feature_name: str) -> Document | None:
        """Load the feature.md Document for a feature."""
        feat_dir = self.find_feature_dir(feature_name)
        if not feat_dir:
            return None
        path = feat_dir / "feature.md"
        return self.load(path) if path.exists() else None

    def read_feature_text(self, feature_name: str) -> str | None:
        """Read the full text of a feature spec."""
        feat_dir = self.find_feature_dir(feature_name)
        if not feat_dir:
            return None
        path = feat_dir / "feature.md"
        return path.read_text(encoding="utf-8") if path.exists() else None

    # ── Story operations ─────────────────────────────────────────

    def list_story_paths(self, feature_name: str) -> list[Path]:
        """Get sorted paths to all story files for a feature."""
        feat_dir = self.find_feature_dir(feature_name)
        if not feat_dir:
            return []
        stories_dir = feat_dir / "stories"
        if not stories_dir.exists():
            return []
        return sorted(stories_dir.glob("STORY_*.md"))

    def list_stories(self, feature_name: str) -> list[Document]:
        """Load all story Documents for a feature."""
        return [self.load(p) for p in self.list_story_paths(feature_name)]

    def list_story_texts(self, feature_name: str) -> list[str]:
        """Read all story files for a feature as raw text."""
        return [p.read_text(encoding="utf-8") for p in self.list_story_paths(feature_name)]

    def get_stories_by_status(self, feature_name: str, status: Status) -> list[Document]:
        """Load all stories with a given status."""
        return [doc for doc in self.list_stories(feature_name) if doc.status == status]

    # ── Task operations ──────────────────────────────────────────

    def list_task_paths(self, ws_story_dir: Path) -> list[Path]:
        """Get sorted paths to all task files in a workstream story directory."""
        if not ws_story_dir.exists():
            return []
        return sorted(ws_story_dir.glob("TASK_*.md"))

    def list_task_texts(self, ws_story_dir: Path) -> list[str]:
        """Read all task files in a workstream story directory as raw text."""
        return [p.read_text(encoding="utf-8") for p in self.list_task_paths(ws_story_dir)]

    # ── Auto-increment helpers ───────────────────────────────────

    def next_number(self, directory: Path, pattern: str) -> int:
        """Scan directory for the highest number matching regex pattern.

        Args:
            directory: Directory to scan.
            pattern: Regex with one capture group for the number,
                     e.g., r"FEAT_(\\d{3})_"

        Returns:
            Next available number (max found + 1, or 1 if none).
        """
        if not directory.exists():
            return 1
        max_num = 0
        for item in directory.iterdir():
            match = re.search(pattern, item.name)
            if match:
                max_num = max(max_num, int(match.group(1)))
        return max_num + 1

    def next_feature_number(self) -> int:
        return self.next_number(self.specs_dir, r"FEAT_(\d{3})_")

    def next_story_number(self, feature_dir: Path) -> int:
        return self.next_number(feature_dir / "stories", r"STORY_(\d{3})")

    def next_task_number(self, ws_story_dir: Path) -> int:
        return self.next_number(ws_story_dir, r"TASK_(\d{3})")
