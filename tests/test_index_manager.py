"""Tests for INDEX.md generation."""

from __future__ import annotations

from pathlib import Path

from sdd.index_manager import IndexManager


class TestIndexManager:
    def test_regenerate_empty_project(self, tmp_project: Path) -> None:
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / "INDEX.md").read_text()
        assert "# SDD Project Index" in index
        assert "No features defined yet" in index
        assert "No workstreams yet" in index

    def test_regenerate_with_feature(self, project_with_feature: Path) -> None:
        mgr = IndexManager(project_with_feature)
        mgr.regenerate()
        index = (project_with_feature / "INDEX.md").read_text()
        assert "FEAT_001_checkout_resume" in index
        assert "Checkout Resume" in index
        assert "[TODO]" in index

    def test_regenerate_with_workstream(self, project_with_workstream: Path) -> None:
        mgr = IndexManager(project_with_workstream)
        mgr.regenerate()
        index = (project_with_workstream / "INDEX.md").read_text()
        assert "WS_001" in index
        assert "FEAT_001_checkout_resume" in index

    def test_regenerate_with_design(self, tmp_project: Path) -> None:
        design_dir = tmp_project / "design"
        (design_dir / "design.md").write_text("# Design")
        (design_dir / "COMP_auth.md").write_text("# Auth Component")

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / "INDEX.md").read_text()
        assert "design.md" in index
        assert "COMP_auth.md" in index

    def test_story_count(self, project_with_stories: Path) -> None:
        mgr = IndexManager(project_with_stories)
        mgr.regenerate()
        index = (project_with_stories / "INDEX.md").read_text()
        assert "(2 stories)" in index
