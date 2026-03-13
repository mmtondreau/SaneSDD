"""Tests for INDEX.md generation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

from ssdd.index_manager import IndexManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _init_git(project: Path) -> None:
    """Initialize a git repo and add all files so git ls-files works."""
    subprocess.run(["git", "init"], cwd=project, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project, capture_output=True)


class TestIndexManager:
    def test_regenerate_empty_project(self, tmp_project: Path) -> None:
        _init_git(tmp_project)
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "# SaneSDD Project Index" in index
        assert "No specifications defined yet" in index
        assert "No epics yet" in index

    def test_regenerate_with_legacy_feature(self, project_with_feature: Path) -> None:
        _init_git(project_with_feature)
        mgr = IndexManager(project_with_feature)
        mgr.regenerate()
        index = (project_with_feature / ".ssdd" / "INDEX.md").read_text()
        assert "FEAT_001_checkout_resume" in index
        assert "Checkout Resume" in index
        assert "[TODO]" in index

    def test_regenerate_with_theme(self, tmp_project: Path) -> None:
        theme_dir = tmp_project / ".ssdd" / "specs" / "THEME_001_ecommerce"
        theme_dir.mkdir(parents=True)
        shutil.copy(FIXTURES_DIR / "sample_theme.md", theme_dir / "theme.md")

        feat_dir = theme_dir / "features" / "FEAT_001_checkout_resume"
        feat_dir.mkdir(parents=True)
        (feat_dir / "stories").mkdir()
        shutil.copy(FIXTURES_DIR / "sample_feature.md", feat_dir / "feature.md")

        _init_git(tmp_project)
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "THEME_001_ecommerce" in index
        assert "E-Commerce" in index
        assert "FEAT_001_checkout_resume" in index

    def test_regenerate_with_epic(self, project_with_epic: Path) -> None:
        _init_git(project_with_epic)
        mgr = IndexManager(project_with_epic)
        mgr.regenerate()
        index = (project_with_epic / ".ssdd" / "INDEX.md").read_text()
        assert "EPIC_001_checkout_resume" in index
        assert "has plan" in index

    def test_regenerate_with_design(self, tmp_project: Path) -> None:
        design_dir = tmp_project / ".ssdd" / "design"
        (design_dir / "design.md").write_text("# Design")
        (design_dir / "COMP_auth.md").write_text("# Auth Component")

        _init_git(tmp_project)
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "design/design.md:" in index
        assert "design/COMP_auth.md:" in index

    def test_regenerate_with_domain(self, tmp_project: Path) -> None:
        domain_dir = tmp_project / ".ssdd" / "design" / "DOMAIN_001_commerce"
        domain_dir.mkdir(parents=True)
        (domain_dir / "domain.md").write_text("# Commerce")
        (domain_dir / "COMP_cart.md").write_text("# Cart")

        _init_git(tmp_project)
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "design/DOMAIN_001_commerce/domain.md:" in index
        assert "design/DOMAIN_001_commerce/COMP_cart.md:" in index

    def test_story_count(self, project_with_stories: Path) -> None:
        _init_git(project_with_stories)
        mgr = IndexManager(project_with_stories)
        mgr.regenerate()
        index = (project_with_stories / ".ssdd" / "INDEX.md").read_text()
        assert "(2 stories)" in index


class TestSourceFiles:
    def test_source_files_section_present(self, tmp_project: Path) -> None:
        """Source Files section appears in generated INDEX.md."""
        (tmp_project / "main.py").write_text("print('hello')")
        _init_git(tmp_project)
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "## Source Files" in index
        assert "- main.py:" in index

    def test_source_files_empty_descriptions(self, tmp_project: Path) -> None:
        """New source files get empty descriptions."""
        (tmp_project / "app.py").write_text("# app")
        (tmp_project / "utils.py").write_text("# utils")
        _init_git(tmp_project)
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "- app.py:" in index
        assert "- utils.py:" in index

    def test_preserves_existing_descriptions(self, tmp_project: Path) -> None:
        """Existing descriptions are preserved across regeneration."""
        (tmp_project / "config.py").write_text("# config")
        _init_git(tmp_project)

        # First regeneration - empty descriptions
        mgr = IndexManager(tmp_project)
        mgr.regenerate()

        # Manually add a description (simulating what the skill would do)
        index_path = tmp_project / ".ssdd" / "INDEX.md"
        content = index_path.read_text()
        content = content.replace("- config.py:", "- config.py: Configuration constants and defaults.")
        index_path.write_text(content)

        # Second regeneration - description should be preserved
        mgr.regenerate()
        index = index_path.read_text()
        assert "- config.py: Configuration constants and defaults." in index

    def test_removes_deleted_files(self, tmp_project: Path) -> None:
        """Files removed from the repo are removed from the index."""
        (tmp_project / "keep.py").write_text("# keep")
        (tmp_project / "delete_me.py").write_text("# delete")
        _init_git(tmp_project)

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "- delete_me.py:" in index

        # Remove file and re-stage
        (tmp_project / "delete_me.py").unlink()
        subprocess.run(["git", "add", "-A"], cwd=tmp_project, capture_output=True)

        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "delete_me.py" not in index
        assert "- keep.py:" in index

    def test_excludes_ssdd_files(self, tmp_project: Path) -> None:
        """Files inside .ssdd/ are excluded from the source files section."""
        (tmp_project / "app.py").write_text("# app")
        _init_git(tmp_project)

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()

        # Source Files section should have app.py but not .ssdd/ files
        source_section = index.split("## Source Files")[1].split("## Specifications")[0]
        assert "- app.py:" in source_section
        assert ".ssdd/" not in source_section

    def test_excludes_binary_files(self, tmp_project: Path) -> None:
        """Binary files are excluded from the source files section."""
        (tmp_project / "app.py").write_text("# app")
        (tmp_project / "image.png").write_bytes(b"\x89PNG")
        _init_git(tmp_project)

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        source_section = index.split("## Source Files")[1].split("## Specifications")[0]
        assert "- app.py:" in source_section
        assert "image.png" not in source_section

    def test_fallback_without_git(self, tmp_project: Path) -> None:
        """Falls back to filesystem walk when git is not available."""
        (tmp_project / "hello.py").write_text("# hello")

        with patch("ssdd.index_manager.subprocess.run", side_effect=FileNotFoundError):
            mgr = IndexManager(tmp_project)
            mgr.regenerate()

        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "## Source Files" in index
        assert "- hello.py:" in index

    def test_no_source_files(self, tmp_project: Path) -> None:
        """Empty project shows placeholder message in source files section."""
        _init_git(tmp_project)
        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "No source files found" in index

    def test_subdirectory_files(self, tmp_project: Path) -> None:
        """Files in subdirectories use relative paths."""
        src_dir = tmp_project / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("# main")
        (src_dir / "utils.py").write_text("# utils")
        _init_git(tmp_project)

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        assert "- src/main.py:" in index
        assert "- src/utils.py:" in index

    def test_adds_new_files_preserves_existing(self, tmp_project: Path) -> None:
        """New files get empty descriptions while existing descriptions are kept."""
        (tmp_project / "old.py").write_text("# old")
        _init_git(tmp_project)

        mgr = IndexManager(tmp_project)
        mgr.regenerate()

        # Add description for old.py
        index_path = tmp_project / ".ssdd" / "INDEX.md"
        content = index_path.read_text()
        content = content.replace("- old.py:", "- old.py: Legacy module.")
        index_path.write_text(content)

        # Add a new file
        (tmp_project / "new.py").write_text("# new")
        subprocess.run(["git", "add", "new.py"], cwd=tmp_project, capture_output=True)

        mgr.regenerate()
        index = index_path.read_text()
        assert "- old.py: Legacy module." in index
        assert "- new.py:" in index

    def test_excludes_egg_info_dirs(self, tmp_project: Path) -> None:
        """Directories matching *.egg-info are excluded from source files."""
        egg_dir = tmp_project / "mypackage.egg-info"
        egg_dir.mkdir()
        (egg_dir / "PKG-INFO").write_text("Metadata-Version: 2.1")
        (tmp_project / "app.py").write_text("# app")
        _init_git(tmp_project)

        mgr = IndexManager(tmp_project)
        mgr.regenerate()
        index = (tmp_project / ".ssdd" / "INDEX.md").read_text()
        source_section = index.split("## Source Files")[1].split("## Specifications")[0]
        assert "- app.py:" in source_section
        assert "egg-info" not in source_section
