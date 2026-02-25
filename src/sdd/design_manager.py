"""Global design/ directory management."""

from __future__ import annotations

from pathlib import Path


class DesignManager:
    """Manages the global design/ directory.

    Contains:
    - design/design.md: overarching system design
    - design/COMP_*.md: component-level design documents
    """

    def __init__(self, project_root: Path) -> None:
        self._dir = project_root / "design"

    def ensure_dir(self) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        return self._dir

    def list_components(self) -> list[Path]:
        if not self._dir.exists():
            return []
        return sorted(self._dir.glob("COMP_*.md"))

    def get_design_summary(self) -> str:
        """Build a concatenated summary of all design docs for prompt context."""
        if not self._dir.exists():
            return ""

        parts: list[str] = []
        main = self._dir / "design.md"
        if main.exists():
            parts.append(f"### Main Design\n\n{main.read_text(encoding='utf-8')}")

        for comp in self.list_components():
            parts.append(f"### {comp.stem}\n\n{comp.read_text(encoding='utf-8')}")

        return "\n\n---\n\n".join(parts)
