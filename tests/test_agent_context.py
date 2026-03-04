"""Tests for agent context persistence."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

import ssdd.util_cli as _util_mod
from ssdd.agent_context import AgentContextManager
from ssdd.util_cli import cli


SAMPLE_CONTEXT = """\
---
role: "system_architect"
skill: "ssdd-design"
feature: "FEAT_001"
workstream: "WS_001"
last_updated: "2026-02-26T14:30:00"
invocation_count: 1
---

## Session Summary
Designed the checkout resume feature.

## Key Decisions
- Use session-based cart storage (rationale: simpler than DB approach)

## Artifacts Modified
- `work/WS_001/FEAT_001_checkout_resume/high_level_design.md` -- created

## Current State
High-level design complete.

## Open Questions
- None

## Context for Next Invocation
Cart storage uses sessions. Design complete.
"""


class TestAgentContextManager:
    def test_context_path_workstream(self, tmp_path: Path) -> None:
        mgr = AgentContextManager()
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        path = mgr.context_path("system_architect", ws_feature_dir=ws_dir)
        assert path == ws_dir / "agent" / "system_architect" / "context.md"

    def test_context_path_feature(self, tmp_path: Path) -> None:
        mgr = AgentContextManager()
        feat_dir = tmp_path / "specs" / "FEAT_001_slug"
        path = mgr.context_path("product_manager", feature_dir=feat_dir)
        assert path == feat_dir / "agent" / "product_manager" / "context.md"

    def test_context_path_requires_dir(self) -> None:
        mgr = AgentContextManager()
        with pytest.raises(ValueError, match="Provide epic_dir, theme_dir, ws_feature_dir, or feature_dir"):
            mgr.context_path("system_architect")

    def test_read_context_returns_none_when_missing(self, tmp_path: Path) -> None:
        mgr = AgentContextManager()
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        result = mgr.read_context("system_architect", ws_feature_dir=ws_dir)
        assert result is None

    def test_read_context_returns_content(self, tmp_path: Path) -> None:
        mgr = AgentContextManager()
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        ctx_path = ws_dir / "agent" / "system_architect" / "context.md"
        ctx_path.parent.mkdir(parents=True)
        ctx_path.write_text(SAMPLE_CONTEXT, encoding="utf-8")

        result = mgr.read_context("system_architect", ws_feature_dir=ws_dir)
        assert result == SAMPLE_CONTEXT

    def test_ensure_context_dir_creates_dirs(self, tmp_path: Path) -> None:
        mgr = AgentContextManager()
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        path = mgr.ensure_context_dir("developer", ws_feature_dir=ws_dir)
        assert path.parent.is_dir()
        assert path == ws_dir / "agent" / "developer" / "context.md"

    def test_ensure_context_dir_idempotent(self, tmp_path: Path) -> None:
        mgr = AgentContextManager()
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        path1 = mgr.ensure_context_dir("developer", ws_feature_dir=ws_dir)
        path2 = mgr.ensure_context_dir("developer", ws_feature_dir=ws_dir)
        assert path1 == path2
        assert path1.parent.is_dir()

    def test_workstream_prefers_over_feature(self, tmp_path: Path) -> None:
        mgr = AgentContextManager()
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        feat_dir = tmp_path / "specs" / "FEAT_001_slug"
        path = mgr.context_path(
            "product_manager", ws_feature_dir=ws_dir, feature_dir=feat_dir
        )
        assert path == ws_dir / "agent" / "product_manager" / "context.md"


class TestContextPathCli:
    def test_workstream_flag(self, tmp_path: Path) -> None:
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        ws_dir.mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(
            cli, ["context-path", "system_architect", "--workstream", str(ws_dir)]
        )
        assert result.exit_code == 0
        assert "agent/system_architect/context.md" in result.output

    def test_feature_flag(self, tmp_path: Path) -> None:
        feat_dir = tmp_path / "specs" / "FEAT_001_slug"
        feat_dir.mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(
            cli, ["context-path", "product_manager", "--feature", str(feat_dir)]
        )
        assert result.exit_code == 0
        assert "agent/product_manager/context.md" in result.output

    def test_no_flags_errors(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["context-path", "system_architect"])
        assert result.exit_code != 0
        assert "Provide --epic, --theme, --workstream, or --feature" in result.output

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["context-path", "developer", "--workstream", str(ws_dir)]
        )
        assert result.exit_code == 0
        agent_dir = ws_dir / "agent" / "developer"
        assert agent_dir.is_dir()


class TestReadContextCli:
    def test_empty_when_no_context(self, tmp_path: Path) -> None:
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        ws_dir.mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(
            cli, ["read-context", "system_architect", "--workstream", str(ws_dir)]
        )
        assert result.exit_code == 0
        assert result.output == ""

    def test_returns_content_when_exists(self, tmp_path: Path) -> None:
        ws_dir = tmp_path / "work" / "WS_001" / "FEAT_001_slug"
        ctx_path = ws_dir / "agent" / "system_architect" / "context.md"
        ctx_path.parent.mkdir(parents=True)
        ctx_path.write_text(SAMPLE_CONTEXT, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli, ["read-context", "system_architect", "--workstream", str(ws_dir)]
        )
        assert result.exit_code == 0
        assert "Session Summary" in result.output
        assert "system_architect" in result.output

    def test_no_flags_errors(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["read-context", "system_architect"])
        assert result.exit_code != 0
        assert "Provide --epic, --theme, --workstream, or --feature" in result.output
