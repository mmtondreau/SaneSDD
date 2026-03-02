"""Tests for INDEX.md generation."""

from __future__ import annotations

import shutil
from pathlib import Path

from sdd.index_manager import IndexManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestIndexManager:
    def test_regenerate_empty_project(self, tmp_project: Path) -> None:
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / "INDEX.md").read_text()
        assert "# SDD Project Index" in index
        assert "No specifications defined yet" in index
        assert "No epics yet" in index

    def test_regenerate_with_legacy_feature(self, project_with_feature: Path) -> None:
        mgr = IndexManager(project_with_feature)
        mgr.regenerate()
        index = (project_with_feature / "INDEX.md").read_text()
        assert "FEAT_001_checkout_resume" in index
        assert "Checkout Resume" in index
        assert "[TODO]" in index

    def test_regenerate_with_theme(self, tmp_project: Path) -> None:
        theme_dir = tmp_project / "specs" / "THEME_001_ecommerce"
        theme_dir.mkdir(parents=True)
        shutil.copy(FIXTURES_DIR / "sample_theme.md", theme_dir / "theme.md")

        feat_dir = theme_dir / "features" / "FEAT_001_checkout_resume"
        feat_dir.mkdir(parents=True)
        (feat_dir / "stories").mkdir()
        shutil.copy(FIXTURES_DIR / "sample_feature.md", feat_dir / "feature.md")

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / "INDEX.md").read_text()
        assert "THEME_001_ecommerce" in index
        assert "E-Commerce" in index
        assert "FEAT_001_checkout_resume" in index

    def test_regenerate_with_epic(self, project_with_epic: Path) -> None:
        mgr = IndexManager(project_with_epic)
        mgr.regenerate()
        index = (project_with_epic / "INDEX.md").read_text()
        assert "EPIC_001_checkout_resume" in index
        assert "has plan" in index

    def test_regenerate_with_design(self, tmp_project: Path) -> None:
        design_dir = tmp_project / "design"
        (design_dir / "design.md").write_text("# Design")
        (design_dir / "COMP_auth.md").write_text("# Auth Component")

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / "INDEX.md").read_text()
        assert "design.md" in index
        assert "COMP_auth.md" in index

    def test_regenerate_with_domain(self, tmp_project: Path) -> None:
        domain_dir = tmp_project / "design" / "DOMAIN_001_commerce"
        domain_dir.mkdir(parents=True)
        (domain_dir / "domain.md").write_text("# Commerce")
        (domain_dir / "COMP_cart.md").write_text("# Cart")

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / "INDEX.md").read_text()
        assert "DOMAIN_001_commerce" in index
        assert "domain.md" in index
        assert "COMP_cart.md" in index

    def test_story_count(self, project_with_stories: Path) -> None:
        mgr = IndexManager(project_with_stories)
        mgr.regenerate()
        index = (project_with_stories / "INDEX.md").read_text()
        assert "(2 stories)" in index
