"""YAML frontmatter state management for SaneSDD artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

import frontmatter

from ssdd.config import DESIGN_DIR, SPECS_DIR, WORK_DIR


class Status(Enum):
    """Valid statuses for any SaneSDD artifact."""
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


@dataclass
class StoryLocation:
    """Result of finding a story by name/ID/slug."""
    story_path: Path
    story_id: str
    feature_dir: Path
    feature_slug: str
    # Optional fields for work-channel stories
    epic_dir: Path | None = None
    epic_slug: str | None = None
    # Optional field for spec-channel stories in theme hierarchy
    theme_dir: Path | None = None


@dataclass
class EpicLocation:
    """Result of finding an epic in work/."""
    epic_dir: Path
    epic_id: str
    epic_slug: str


_STORY_GLOB = "STORY_*.md"


class StateManager:
    """Reads and writes YAML-frontmatter markdown files."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root

    @property
    def specs_dir(self) -> Path:
        return self._root / SPECS_DIR

    @property
    def work_dir(self) -> Path:
        return self._root / WORK_DIR

    @property
    def design_dir(self) -> Path:
        return self._root / DESIGN_DIR

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
        """Find a feature directory by exact name or substring match.

        Searches both the new theme hierarchy (specs/THEME_*/features/FEAT_*)
        and the legacy flat layout (specs/FEAT_*).
        """
        # New hierarchy: specs/THEME_*/features/FEAT_*
        result = self.find_feature_in_specs(feature_name)
        if result:
            return result

        # Legacy flat layout: specs/FEAT_*
        if not self.specs_dir.exists():
            return None
        for d in sorted(self.specs_dir.iterdir()):
            if d.is_dir() and d.name.startswith("FEAT_") and (
                d.name == feature_name or feature_name in d.name
            ):
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
        return sorted(stories_dir.glob(_STORY_GLOB))

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

    def _collect_stories_from(self, feat_dir: Path) -> list[tuple[Path, Path]]:
        """Collect (feature_dir, story_file) pairs from a single feature directory."""
        stories_dir = feat_dir / "stories"
        if not stories_dir.exists():
            return []
        return [(feat_dir, f) for f in sorted(stories_dir.glob(_STORY_GLOB))]

    def _list_feature_dirs(self) -> list[Path]:
        """List all FEAT_* directories across themes and legacy layout."""
        dirs: list[Path] = []
        # New hierarchy: specs/THEME_*/features/FEAT_*
        for theme_dir in self._list_theme_dirs():
            features_dir = theme_dir / "features"
            if features_dir.exists():
                dirs.extend(
                    d for d in sorted(features_dir.iterdir())
                    if d.is_dir() and d.name.startswith("FEAT_")
                )
        # Legacy flat layout: specs/FEAT_*
        if self.specs_dir.exists():
            dirs.extend(
                d for d in sorted(self.specs_dir.iterdir())
                if d.is_dir() and d.name.startswith("FEAT_")
            )
        return dirs

    def _story_files(self) -> list[tuple[Path, Path]]:
        """Return (feature_dir, story_file) pairs across all features.

        Searches both the new theme hierarchy (specs/THEME_*/features/FEAT_*)
        and the legacy flat layout (specs/FEAT_*).
        """
        results: list[tuple[Path, Path]] = []
        for feat_dir in self._list_feature_dirs():
            results.extend(self._collect_stories_from(feat_dir))
        return results

    @staticmethod
    def _extract_story_id(stem: str) -> str:
        """Extract STORY_NNN from a filename stem like STORY_001_user_login."""
        id_match = re.match(r"(STORY_\d{3})", stem)
        return id_match.group(1) if id_match else stem

    def find_story(self, name: str, channel: str = "both") -> StoryLocation | None:
        """Find a story by exact ID, slug, or substring match.

        Args:
            name: Story name, ID, or substring to search for.
            channel: "spec" to search specs only, "work" to search work only,
                     "both" to search both (default).
        """
        if channel in ("spec", "both"):
            for feat_dir, story_file in self._story_files():
                stem = story_file.stem
                story_id = self._extract_story_id(stem)
                if stem == name or story_id == name or name in stem:
                    return StoryLocation(
                        story_path=story_file,
                        story_id=story_id,
                        feature_dir=feat_dir,
                        feature_slug=feat_dir.name,
                    )
        if channel in ("work", "both"):
            return self.find_work_story(name)
        return None

    def next_feature_number(self) -> int:
        return self.next_number(self.specs_dir, r"FEAT_(\d{3})_")

    def next_story_number(self, feature_dir: Path) -> int:
        return self.next_number(feature_dir / "stories", r"STORY_(\d{3})")

    def next_task_number(self, ws_story_dir: Path) -> int:
        return self.next_number(ws_story_dir, r"TASK_(\d{3})")

    # ── Theme operations ──────────────────────────────────────────

    def find_theme_dir(self, theme_name: str) -> Path | None:
        """Find a theme directory by exact name or substring match."""
        if not self.specs_dir.exists():
            return None
        for d in sorted(self.specs_dir.iterdir()):
            if d.is_dir() and d.name.startswith("THEME_") and (
                d.name == theme_name or theme_name in d.name
            ):
                return d
        return None

    def next_theme_number(self) -> int:
        """Return the next available THEME_NNN number."""
        return self.next_number(self.specs_dir, r"THEME_(\d{3})_")

    def next_feature_number_in_theme(self, theme_dir: Path) -> int:
        """Return the next available FEAT_NNN number within a theme."""
        return self.next_number(theme_dir / "features", r"FEAT_(\d{3})_")

    def _list_theme_dirs(self) -> list[Path]:
        """Return sorted THEME_* directories under specs/."""
        if not self.specs_dir.exists():
            return []
        return sorted(
            d for d in self.specs_dir.iterdir()
            if d.is_dir() and d.name.startswith("THEME_")
        )

    def find_feature_in_specs(self, feature_name: str) -> Path | None:
        """Find a feature directory within the theme hierarchy.

        Scans specs/THEME_*/features/ for matching FEAT_* directories.
        """
        for theme_dir in self._list_theme_dirs():
            features_dir = theme_dir / "features"
            if not features_dir.exists():
                continue
            for feat_dir in sorted(features_dir.iterdir()):
                if feat_dir.is_dir() and (
                    feat_dir.name == feature_name or feature_name in feat_dir.name
                ):
                    return feat_dir
        return None

    # ── Work-channel story operations ─────────────────────────────

    def _work_story_files(self) -> list[tuple[Path, Path]]:
        """Return (epic_dir, story_file) pairs across all epics."""
        if not self.work_dir.exists():
            return []
        results: list[tuple[Path, Path]] = []
        for epic_dir in sorted(self.work_dir.iterdir()):
            if not epic_dir.is_dir() or not epic_dir.name.startswith("EPIC_"):
                continue
            stories_dir = epic_dir / "stories"
            if not stories_dir.exists():
                continue
            for story_dir in sorted(stories_dir.iterdir()):
                if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                    continue
                story_file = story_dir / "story.md"
                if story_file.exists():
                    results.append((epic_dir, story_file))
        return results

    def find_work_story(self, name: str) -> StoryLocation | None:
        """Find a work-channel story by exact ID, slug, or substring match."""
        for epic_dir, story_file in self._work_story_files():
            story_dir_name = story_file.parent.name
            story_id = self._extract_story_id(story_dir_name)
            if story_dir_name == name or story_id == name or name in story_dir_name:
                return StoryLocation(
                    story_path=story_file,
                    story_id=story_id,
                    feature_dir=epic_dir,  # for backward compat
                    feature_slug=epic_dir.name,
                    epic_dir=epic_dir,
                    epic_slug=epic_dir.name,
                )
        return None
