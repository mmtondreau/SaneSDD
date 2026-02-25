"""INDEX.md auto-generation from filesystem state."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sdd.state import StateManager


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

        self._append_features_section(lines)
        self._append_workstreams_section(lines)
        self._append_design_section(lines)

        index_path = self._root / "INDEX.md"
        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _append_features_section(self, lines: list[str]) -> None:
        lines.append("## Features")
        lines.append("")
        specs_dir = self._root / "specs"
        feat_dirs = (
            sorted(d for d in specs_dir.iterdir() if d.is_dir() and d.name.startswith("FEAT_"))
            if specs_dir.exists()
            else []
        )
        if not feat_dirs:
            lines.append("_No features defined yet._")
            lines.append("")
            return

        for feat_dir in feat_dirs:
            if not feat_dir.is_dir() or not feat_dir.name.startswith("FEAT_"):
                continue

            feature_md = feat_dir / "feature.md"
            status = "DRAFT"
            title = feat_dir.name
            if feature_md.exists():
                doc = self._state.load(feature_md)
                status = doc.metadata.get("status", "DRAFT")
                title = doc.metadata.get("title", feat_dir.name)

            stories_dir = feat_dir / "stories"
            story_count = len(list(stories_dir.glob("STORY_*.md"))) if stories_dir.exists() else 0

            lines.append(
                f"- **{feat_dir.name}**: {title} `[{status}]` ({story_count} stories)"
            )

        lines.append("")

    def _append_workstreams_section(self, lines: list[str]) -> None:
        lines.append("## Workstreams")
        lines.append("")
        work_dir = self._root / "work"
        ws_dirs = (
            sorted(d for d in work_dir.iterdir() if d.is_dir() and d.name.startswith("WS_"))
            if work_dir.exists()
            else []
        )
        if not ws_dirs:
            lines.append("_No workstreams yet._")
            lines.append("")
            return

        for ws_dir in ws_dirs:
            features = [d.name for d in sorted(ws_dir.iterdir()) if d.is_dir()]
            has_plan = any(
                (ws_dir / f / "development_plan.yaml").exists() for f in features
            )
            plan_marker = " (has plan)" if has_plan else ""
            lines.append(f"- **{ws_dir.name}**: {', '.join(features)}{plan_marker}")

        lines.append("")

    def _append_design_section(self, lines: list[str]) -> None:
        lines.append("## Design Documents")
        lines.append("")
        design_dir = self._root / "design"
        if not design_dir.exists():
            lines.append("_No design documents yet._")
            lines.append("")
            return

        for doc_file in sorted(design_dir.glob("*.md")):
            lines.append(f"- [{doc_file.name}](design/{doc_file.name})")

        lines.append("")
