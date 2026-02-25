"""Workstream lifecycle management under work/."""

from __future__ import annotations

import re
from pathlib import Path


class WorkstreamManager:
    """Manages workstream directories under work/.

    Each workstream (WS_001, WS_002, ...) represents one design+implementation
    pass for a feature. Running `sdd design` always creates a new workstream.
    """

    def __init__(self, project_root: Path) -> None:
        self._work_dir = project_root / "work"

    def next_number(self) -> int:
        """Scan work/ for WS_### directories and return the next number."""
        if not self._work_dir.exists():
            return 1
        max_num = 0
        for d in self._work_dir.iterdir():
            if d.is_dir():
                match = re.match(r"WS_(\d{3})$", d.name)
                if match:
                    max_num = max(max_num, int(match.group(1)))
        return max_num + 1

    def create(self, feature_slug: str) -> Path:
        """Create a new workstream with scaffolding for a feature.

        Args:
            feature_slug: e.g., "FEAT_001_checkout_resume"

        Returns:
            Path to the workstream's feature directory:
            work/WS_###/FEAT_001_checkout_resume/
        """
        ws_num = self.next_number()
        ws_name = f"WS_{ws_num:03d}"
        feat_dir = self._work_dir / ws_name / feature_slug
        feat_dir.mkdir(parents=True, exist_ok=True)
        (feat_dir / "stories").mkdir(exist_ok=True)
        return feat_dir

    def find_active(self, feature_name: str | None = None) -> Path | None:
        """Find the most recent workstream, optionally for a specific feature.

        Returns:
            Path to work/WS_###/ or work/WS_###/FEAT_*/ or None.
        """
        if not self._work_dir.exists():
            return None

        ws_dirs = sorted(
            [d for d in self._work_dir.iterdir()
             if d.is_dir() and re.match(r"WS_\d{3}$", d.name)],
            key=lambda d: d.name,
        )
        if not ws_dirs:
            return None

        latest_ws = ws_dirs[-1]

        if not feature_name:
            return latest_ws

        for sub in sorted(latest_ws.iterdir()):
            if sub.is_dir() and (sub.name == feature_name or feature_name in sub.name):
                return sub
        return None

    def scaffold_story_dir(self, ws_feature_dir: Path, story_id: str) -> Path:
        """Create a task directory for a story within a workstream."""
        story_dir = ws_feature_dir / "stories" / story_id
        story_dir.mkdir(parents=True, exist_ok=True)
        return story_dir

    def list_workstreams(self) -> list[Path]:
        """List all workstream directories in order."""
        if not self._work_dir.exists():
            return []
        return sorted(
            [d for d in self._work_dir.iterdir()
             if d.is_dir() and re.match(r"WS_\d{3}$", d.name)],
            key=lambda d: d.name,
        )
