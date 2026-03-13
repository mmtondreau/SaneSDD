"""INDEX.md auto-generation from filesystem state."""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

from ssdd.config import DESIGN_DIR, INDEX_FILE, SPECS_DIR, SSDD_DIR, WORK_DIR
from ssdd.state import StateManager, _STORY_GLOB

# Regex to parse source file entries: `- path/to/file: description` or `- path/to/file:`
_SOURCE_ENTRY_RE = re.compile(r"^- (.+?):\s*(.*)$")

# File extensions to exclude from source file listing
_BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".pyc", ".pyo", ".class", ".o", ".so", ".dylib", ".dll",
    ".exe", ".bin",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".db", ".sqlite", ".sqlite3",
})

# Directories to always exclude (relative to project root)
_EXCLUDED_DIRS = frozenset({
    ".ssdd", ".git", ".claude", "node_modules", "__pycache__",
    ".venv", "venv", ".env", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build",
    ".eggs", "*.egg-info",
})


class IndexManager:
    """Regenerates INDEX.md from filesystem state.

    INDEX.md is auto-generated after each sdd command completes.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._state = StateManager(project_root)

    def regenerate(self) -> None:
        # Parse existing descriptions before overwriting
        existing_descriptions = self._parse_existing_source_descriptions()

        lines: list[str] = [
            "# SaneSDD Project Index",
            "",
            f"_Auto-generated: {date.today().isoformat()}_",
            "",
        ]

        self._append_source_files_section(lines, existing_descriptions)
        self._append_specs_section(lines)
        self._append_epics_section(lines)
        self._append_design_section(lines)

        index_path = self._root / INDEX_FILE
        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _parse_existing_source_descriptions(self) -> dict[str, str]:
        """Read current INDEX.md and extract file: description pairs from Source Files section."""
        index_path = self._root / INDEX_FILE
        if not index_path.exists():
            return {}

        descriptions: dict[str, str] = {}
        in_source_section = False

        for line in index_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## Source Files"):
                in_source_section = True
                continue
            if in_source_section and line.startswith("## "):
                break
            if in_source_section:
                m = _SOURCE_ENTRY_RE.match(line)
                if m:
                    filepath, desc = m.group(1).strip(), m.group(2).strip()
                    descriptions[filepath] = desc

        return descriptions

    def _collect_source_files(self) -> list[str]:
        """Collect source files from the repo, using git ls-files if available."""
        files: list[str] = []

        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self._root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                files = [f for f in result.stdout.strip().splitlines() if f]
            else:
                files = self._collect_source_files_fallback()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            files = self._collect_source_files_fallback()

        return self._filter_source_files(sorted(files))

    def _collect_source_files_fallback(self) -> list[str]:
        """Walk the filesystem when git is not available."""
        files: list[str] = []
        for path in self._root.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(self._root))
            files.append(rel)
        return files

    @staticmethod
    def _is_excluded_dir(part: str) -> bool:
        """Check if a path component matches an excluded directory pattern."""
        if part in _EXCLUDED_DIRS:
            return True
        # Handle glob-style patterns like *.egg-info
        return any(
            pat.startswith("*") and part.endswith(pat[1:])
            for pat in _EXCLUDED_DIRS
            if "*" in pat
        )

    def _filter_source_files(self, files: list[str]) -> list[str]:
        """Filter out .ssdd/, binary files, and excluded directories."""
        filtered: list[str] = []
        for f in files:
            parts = Path(f).parts
            # Skip files in excluded directories
            if any(self._is_excluded_dir(part) for part in parts):
                continue
            # Skip binary files by extension
            if Path(f).suffix.lower() in _BINARY_EXTENSIONS:
                continue
            filtered.append(f)
        return filtered

    def _append_source_files_section(
        self, lines: list[str], existing_descriptions: dict[str, str]
    ) -> None:
        """Append source files with preserved descriptions."""
        lines.append("## Source Files")
        lines.append("")

        source_files = self._collect_source_files()
        if not source_files:
            lines.append("_No source files found._")
            lines.append("")
            return

        for filepath in source_files:
            desc = existing_descriptions.get(filepath, "")
            if desc:
                lines.append(f"- {filepath}: {desc}")
            else:
                lines.append(f"- {filepath}:")

        lines.append("")

    def _append_specs_section(self, lines: list[str]) -> None:
        """Append themes/features/stories from the spec channel."""
        lines.append("## Specifications")
        lines.append("")
        specs_dir = self._root / SPECS_DIR

        theme_dirs = self._state._list_theme_dirs()
        legacy_feat_dirs = self._legacy_feat_dirs(specs_dir)

        if not theme_dirs and not legacy_feat_dirs:
            lines.append("_No specifications defined yet._")
            lines.append("")
            return

        for theme_dir in theme_dirs:
            self._append_theme_entry(lines, theme_dir)

        for feat_dir in legacy_feat_dirs:
            self._append_feature_entry(lines, feat_dir, indent="")

        lines.append("")

    @staticmethod
    def _legacy_feat_dirs(specs_dir: Path) -> list[Path]:
        if not specs_dir.exists():
            return []
        return sorted(
            d for d in specs_dir.iterdir()
            if d.is_dir() and d.name.startswith("FEAT_")
        )

    def _append_theme_entry(self, lines: list[str], theme_dir: Path) -> None:
        theme_md = theme_dir / "theme.md"
        theme_title = theme_dir.name
        theme_status = "DRAFT"
        if theme_md.exists():
            doc = self._state.load(theme_md)
            theme_title = doc.metadata.get("title", theme_dir.name)
            theme_status = doc.metadata.get("status", "DRAFT")
        lines.append(f"- {theme_dir.name}: {theme_title} `[{theme_status}]`")

        features_dir = theme_dir / "features"
        if not features_dir.exists():
            return
        for feat_dir in sorted(features_dir.iterdir()):
            if feat_dir.is_dir() and feat_dir.name.startswith("FEAT_"):
                self._append_feature_entry(lines, feat_dir, indent="  ")

    def _append_feature_entry(
        self, lines: list[str], feat_dir: Path, indent: str
    ) -> None:
        feature_md = feat_dir / "feature.md"
        status = "DRAFT"
        title = feat_dir.name
        if feature_md.exists():
            doc = self._state.load(feature_md)
            status = doc.metadata.get("status", "DRAFT")
            title = doc.metadata.get("title", feat_dir.name)

        stories_dir = feat_dir / "stories"
        story_count = (
            len(list(stories_dir.glob(_STORY_GLOB)))
            if stories_dir.exists()
            else 0
        )

        lines.append(
            f"{indent}- {feat_dir.name}: {title} "
            f"`[{status}]` ({story_count} stories)"
        )

    def _append_epics_section(self, lines: list[str]) -> None:
        """Append epics from the work channel."""
        lines.append("## Epics")
        lines.append("")
        work_dir = self._root / WORK_DIR
        epic_dirs = (
            sorted(
                d for d in work_dir.iterdir()
                if d.is_dir() and re.match(r"EPIC_\d{3}_", d.name)
            )
            if work_dir.exists()
            else []
        )

        if not epic_dirs:
            lines.append("_No epics yet._")
            lines.append("")
            return

        for epic_dir in epic_dirs:
            has_plan = (epic_dir / "development_plan.yaml").exists()
            plan_marker = " (has plan)" if has_plan else ""

            epic_md = epic_dir / "epic.md"
            title = epic_dir.name
            status = "DRAFT"
            if epic_md.exists():
                doc = self._state.load(epic_md)
                title = doc.metadata.get("title", epic_dir.name)
                status = doc.metadata.get("status", "DRAFT")

            lines.append(
                f"- {epic_dir.name}: {title} `[{status}]`{plan_marker}"
            )

        lines.append("")

    def _append_design_section(self, lines: list[str]) -> None:
        lines.append("## Design Documents")
        lines.append("")
        design_dir = self._root / DESIGN_DIR
        if not design_dir.exists():
            lines.append("_No design documents yet._")
            lines.append("")
            return

        # Top-level design files
        for doc_file in sorted(design_dir.glob("*.md")):
            lines.append(f"- design/{doc_file.name}:")

        # Domain directories
        for domain_dir in sorted(design_dir.iterdir()):
            if not domain_dir.is_dir() or not domain_dir.name.startswith("DOMAIN_"):
                continue
            for doc_file in sorted(domain_dir.glob("*.md")):
                lines.append(
                    f"- design/{domain_dir.name}/{doc_file.name}:"
                )

        lines.append("")
