"""Persistent context management for agent roles across invocations."""

from __future__ import annotations

from pathlib import Path


class AgentContextManager:
    """Manages persistent context files for agent roles.

    Context files live at:
    - Epic-scoped: work/EPIC_NNN_slug/agent/<role>/context.md
    - Theme-scoped (pre-epic): specs/THEME_NNN_slug/agent/<role>/context.md

    Legacy paths are also supported:
    - Workstream-scoped: work/WS_NNN/FEAT_NNN_slug/agent/<role>/context.md
    - Feature-scoped: specs/FEAT_NNN_slug/agent/<role>/context.md
    """

    def context_path(
        self,
        role: str,
        *,
        epic_dir: Path | None = None,
        theme_dir: Path | None = None,
        # Legacy parameter names (aliases)
        ws_feature_dir: Path | None = None,
        feature_dir: Path | None = None,
    ) -> Path:
        """Resolve the context file path for a role.

        Args:
            role: The agent role identifier (e.g., "system_architect").
            epic_dir: Epic directory (e.g., work/EPIC_001_slug/).
            theme_dir: Theme spec directory (e.g., specs/THEME_001_slug/).
            ws_feature_dir: Legacy: workstream feature directory.
            feature_dir: Legacy: feature spec directory.

        Returns:
            Resolved path to the context.md file.

        Raises:
            ValueError: If no directory is provided.
        """
        base = epic_dir or ws_feature_dir or theme_dir or feature_dir
        if base is None:
            msg = "Provide epic_dir, theme_dir, ws_feature_dir, or feature_dir"
            raise ValueError(msg)
        return base / "agent" / role / "context.md"

    def read_context(
        self,
        role: str,
        *,
        epic_dir: Path | None = None,
        theme_dir: Path | None = None,
        ws_feature_dir: Path | None = None,
        feature_dir: Path | None = None,
    ) -> str | None:
        """Read the context file for a role if it exists.

        Returns:
            File contents as a string, or None if the file does not exist.
        """
        path = self.context_path(
            role,
            epic_dir=epic_dir,
            theme_dir=theme_dir,
            ws_feature_dir=ws_feature_dir,
            feature_dir=feature_dir,
        )
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def ensure_context_dir(
        self,
        role: str,
        *,
        epic_dir: Path | None = None,
        theme_dir: Path | None = None,
        ws_feature_dir: Path | None = None,
        feature_dir: Path | None = None,
    ) -> Path:
        """Create the context directory if needed and return the context file path.

        Returns:
            Path to the context.md file (parent directories created).
        """
        path = self.context_path(
            role,
            epic_dir=epic_dir,
            theme_dir=theme_dir,
            ws_feature_dir=ws_feature_dir,
            feature_dir=feature_dir,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
