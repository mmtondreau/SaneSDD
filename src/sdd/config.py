"""Path constants and project root detection."""

from __future__ import annotations

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from start looking for a directory containing specs/ or .git."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        if (directory / "specs").is_dir() or (directory / ".git").is_dir():
            return directory
    return current


# Standard directory names
SPECS_DIR = "specs"
WORK_DIR = "work"
DESIGN_DIR = "design"
ROLES_DIR = ".roles"
INDEX_FILE = "INDEX.md"
