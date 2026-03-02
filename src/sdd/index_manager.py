"""INDEX.md auto-generation from filesystem state."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from sdd.state import StateManager, _STORY_GLOB


class IndexManager:
    """Regenerates INDEX.md from filesystem state.

    INDEX.md is auto-generated after each sdd command completes.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._state = StateManager(project_root)

    def regenerate(self) -> None:
        lines: list[str] = [
            "# SDD Project Index",
            "",
            f"_Auto-generated: {date.today().isoformat()}_",
            "",
        ]

        self._append_specs_section(lines)
        self._append_epics_section(lines)
        self._append_design_section(lines)

        index_path = self._root / "INDEX.md"
        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _append_specs_section(self, lines: list[str]) -> None:
        """Append themes/features/stories from the spec channel."""
        lines.append("## Specifications")
        lines.append("")
        specs_dir = self._root / "specs"

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
        lines.append(f"- **{theme_dir.name}**: {theme_title} `[{theme_status}]`")

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
            f"{indent}- **{feat_dir.name}**: {title} "
            f"`[{status}]` ({story_count} stories)"
        )

    def _append_epics_section(self, lines: list[str]) -> None:
        """Append epics from the work channel."""
        lines.append("## Epics")
        lines.append("")
        work_dir = self._root / "work"
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
                f"- **{epic_dir.name}**: {title} `[{status}]`{plan_marker}"
            )

        lines.append("")

    def _append_design_section(self, lines: list[str]) -> None:
        lines.append("## Design Documents")
        lines.append("")
        design_dir = self._root / "design"
        if not design_dir.exists():
            lines.append("_No design documents yet._")
            lines.append("")
            return

        # Top-level design files
        for doc_file in sorted(design_dir.glob("*.md")):
            lines.append(f"- [{doc_file.name}](design/{doc_file.name})")

        # Domain directories
        for domain_dir in sorted(design_dir.iterdir()):
            if not domain_dir.is_dir() or not domain_dir.name.startswith("DOMAIN_"):
                continue
            lines.append(f"- **{domain_dir.name}/**")
            for doc_file in sorted(domain_dir.glob("*.md")):
                lines.append(
                    f"  - [{doc_file.name}](design/{domain_dir.name}/{doc_file.name})"
                )

        lines.append("")
