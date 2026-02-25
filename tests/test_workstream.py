"""Tests for workstream management."""

from __future__ import annotations

from pathlib import Path

from sdd.workstream import WorkstreamManager


class TestWorkstreamManager:
    def test_next_number_empty(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        assert ws.next_number() == 1

    def test_create_workstream(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        feat_dir = ws.create("FEAT_001_auth")
        assert feat_dir.exists()
        assert feat_dir.name == "FEAT_001_auth"
        assert feat_dir.parent.name == "WS_001"
        assert (feat_dir / "stories").exists()

    def test_auto_increment(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        ws.create("FEAT_001_auth")
        ws.create("FEAT_001_auth")
        assert ws.next_number() == 3

    def test_find_active_no_workstreams(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        assert ws.find_active() is None

    def test_find_active_latest(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        ws.create("FEAT_001_auth")
        ws.create("FEAT_002_cart")
        result = ws.find_active()
        assert result is not None
        assert result.name == "WS_002"

    def test_find_active_for_feature(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        ws.create("FEAT_001_auth")
        result = ws.find_active("auth")
        assert result is not None
        assert "FEAT_001_auth" in result.name

    def test_find_active_feature_not_found(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        ws.create("FEAT_001_auth")
        result = ws.find_active("nonexistent")
        assert result is None

    def test_scaffold_story_dir(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        feat_dir = ws.create("FEAT_001_auth")
        story_dir = ws.scaffold_story_dir(feat_dir, "STORY_001")
        assert story_dir.exists()
        assert story_dir.name == "STORY_001"

    def test_list_workstreams(self, tmp_project: Path) -> None:
        ws = WorkstreamManager(tmp_project)
        ws.create("FEAT_001_auth")
        ws.create("FEAT_002_cart")
        workstreams = ws.list_workstreams()
        assert len(workstreams) == 2
        assert workstreams[0].name == "WS_001"
        assert workstreams[1].name == "WS_002"
