"""Persistent context management for agent roles across invocations."""

from __future__ import annotations

from pathlib import Path


class AgentContextManager:
    """Manages persistent context files for agent roles.

    Context files live at:
    - Workstream-scoped: work/WS_NNN/FEAT_NNN_slug/agent/<role>/context.md
    - Feature-scoped (pre-workstream): specs/FEAT_NNN_slug/agent/<role>/context.md
    """

    def context_path(
        self,
        role: str,
        *,
        ws_feature_dir: Path | None = None,
        feature_dir: Path | None = None,
    ) -> Path:
        """Resolve the context file path for a role.

        Args:
            role: The agent role identifier (e.g., "system_architect").
            ws_feature_dir: Workstream feature directory
                (e.g., work/WS_001/FEAT_001_slug/).
            feature_dir: Feature spec directory
                (e.g., specs/FEAT_001_slug/). Used for pre-workstream roles.

        Returns:
            Resolved path to the context.md file.

        Raises:
            ValueError: If neither ws_feature_dir nor feature_dir is provided.
        """
        base = ws_feature_dir or feature_dir
        if base is None:
            msg = "Either ws_feature_dir or feature_dir must be provided"
            raise ValueError(msg)
        return base / "agent" / role / "context.md"

    def read_context(
        self,
        role: str,
        *,
        ws_feature_dir: Path | None = None,
        feature_dir: Path | None = None,
    ) -> str | None:
        """Read the context file for a role if it exists.

        Returns:
            File contents as a string, or None if the file does not exist.
        """
        path = self.context_path(
            role, ws_feature_dir=ws_feature_dir, feature_dir=feature_dir
        )
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def ensure_context_dir(
        self,
        role: str,
        *,
        ws_feature_dir: Path | None = None,
        feature_dir: Path | None = None,
    ) -> Path:
        """Create the context directory if needed and return the context file path.

        Returns:
            Path to the context.md file (parent directories created).
        """
        path = self.context_path(
            role, ws_feature_dir=ws_feature_dir, feature_dir=feature_dir
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
