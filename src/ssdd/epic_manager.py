"""Epic lifecycle management under .ssdd/work/."""

from __future__ import annotations

import re
from pathlib import Path

from ssdd.config import WORK_DIR


class EpicManager:
    """Manages epic directories under .ssdd/work/.

    Each epic (EPIC_001, EPIC_002, ...) is a self-contained unit of work.
    Epics replace workstreams entirely.
    """

    def __init__(self, project_root: Path) -> None:
        self._work_dir = project_root / WORK_DIR

    def next_number(self) -> int:
        """Scan work/ for EPIC_### directories and return the next number."""
        if not self._work_dir.exists():
            return 1
        max_num = 0
        for d in self._work_dir.iterdir():
            if d.is_dir():
                match = re.match(r"EPIC_(\d{3})_", d.name)
                if match:
                    max_num = max(max_num, int(match.group(1)))
        return max_num + 1

    def create(self, epic_slug: str) -> Path:
        """Create a new epic with scaffolding.

        Args:
            epic_slug: e.g., "checkout_resume" (without EPIC_NNN prefix).

        Returns:
            Path to the epic directory: work/EPIC_NNN_slug/
        """
        epic_num = self.next_number()
        epic_name = f"EPIC_{epic_num:03d}_{epic_slug}"
        epic_dir = self._work_dir / epic_name
        epic_dir.mkdir(parents=True, exist_ok=True)
        (epic_dir / "stories").mkdir(exist_ok=True)
        return epic_dir

    def find_epic(self, name: str) -> Path | None:
        """Find an epic directory by exact name or substring match."""
        if not self._work_dir.exists():
            return None
        for d in sorted(self._work_dir.iterdir()):
            if d.is_dir() and d.name.startswith("EPIC_") and (
                d.name == name or name in d.name
            ):
                return d
        return None

    def scaffold_story_dir(self, epic_dir: Path, story_id: str) -> Path:
        """Create a story directory within an epic."""
        story_dir = epic_dir / "stories" / story_id
        story_dir.mkdir(parents=True, exist_ok=True)
        return story_dir

    def list_epics(self) -> list[Path]:
        """List all epic directories in order."""
        if not self._work_dir.exists():
            return []
        return sorted(
            d for d in self._work_dir.iterdir()
            if d.is_dir() and re.match(r"EPIC_\d{3}_", d.name)
        )
