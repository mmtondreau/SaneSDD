"""Global .ssdd/design/ directory management."""

from __future__ import annotations

import re
from pathlib import Path

from ssdd.config import DESIGN_DIR


_COMP_GLOB = "COMP_*.md"


class DesignManager:
    """Manages the global .ssdd/design/ directory.

    Contains:
    - .ssdd/design/design.md: overarching system design
    - .ssdd/design/DOMAIN_NNN_slug/domain.md: bounded context descriptions
    - .ssdd/design/DOMAIN_NNN_slug/COMP_*.md: component-level design documents
    """

    def __init__(self, project_root: Path) -> None:
        self._dir = project_root / DESIGN_DIR

    def ensure_dir(self) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        return self._dir

    # ── Domain operations ─────────────────────────────────────────

    def list_domains(self) -> list[Path]:
        """List all DOMAIN_NNN_* directories in order."""
        if not self._dir.exists():
            return []
        return sorted(
            d for d in self._dir.iterdir()
            if d.is_dir() and re.match(r"DOMAIN_\d{3}_", d.name)
        )

    def find_domain(self, name: str) -> Path | None:
        """Find a domain directory by exact name or substring match."""
        if not self._dir.exists():
            return None
        for d in sorted(self._dir.iterdir()):
            if d.is_dir() and d.name.startswith("DOMAIN_") and (
                d.name == name or name in d.name
            ):
                return d
        return None

    def next_domain_number(self) -> int:
        """Return the next available DOMAIN_NNN number."""
        if not self._dir.exists():
            return 1
        max_num = 0
        for d in self._dir.iterdir():
            if d.is_dir():
                match = re.match(r"DOMAIN_(\d{3})_", d.name)
                if match:
                    max_num = max(max_num, int(match.group(1)))
        return max_num + 1

    # ── Component operations ──────────────────────────────────────

    def list_components(self, domain_dir: Path | None = None) -> list[Path]:
        """List component files, optionally scoped to a domain.

        If domain_dir is given, list COMP_*.md within that domain.
        If None, list all COMP_*.md across all domains.
        """
        if domain_dir:
            if not domain_dir.exists():
                return []
            return sorted(domain_dir.glob(_COMP_GLOB))

        if not self._dir.exists():
            return []

        results: list[Path] = []
        # Components inside domain directories
        for domain in self.list_domains():
            results.extend(sorted(domain.glob(_COMP_GLOB)))
        # Legacy: top-level components (for backward compat during migration)
        results.extend(sorted(self._dir.glob(_COMP_GLOB)))
        return results

    def get_design_summary(self) -> str:
        """Build a concatenated summary of all design docs for prompt context."""
        if not self._dir.exists():
            return ""

        parts: list[str] = []
        main = self._dir / "design.md"
        if main.exists():
            parts.append(f"### Main Design\n\n{main.read_text(encoding='utf-8')}")

        for domain_dir in self.list_domains():
            domain_md = domain_dir / "domain.md"
            if domain_md.exists():
                parts.append(
                    f"### Domain: {domain_dir.name}\n\n"
                    f"{domain_md.read_text(encoding='utf-8')}"
                )
            for comp in sorted(domain_dir.glob(_COMP_GLOB)):
                parts.append(f"### {comp.stem}\n\n{comp.read_text(encoding='utf-8')}")

        # Legacy: top-level components outside domains
        for comp in sorted(self._dir.glob(_COMP_GLOB)):
            parts.append(f"### {comp.stem}\n\n{comp.read_text(encoding='utf-8')}")

        return "\n\n---\n\n".join(parts)
