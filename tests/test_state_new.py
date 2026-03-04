"""Tests for new state management methods (themes, epics, work stories)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ssdd.state import EpicLocation, StateManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def project_with_theme(tmp_project: Path) -> Path:
    """Project with a theme and feature in the new hierarchy."""
    theme_dir = tmp_project / ".ssdd" / "specs" / "THEME_001_ecommerce"
    theme_dir.mkdir(parents=True)
    shutil.copy(FIXTURES_DIR / "sample_theme.md", theme_dir / "theme.md")

    feat_dir = theme_dir / "features" / "FEAT_001_checkout_resume"
    feat_dir.mkdir(parents=True)
    (feat_dir / "stories").mkdir()
    shutil.copy(FIXTURES_DIR / "sample_feature.md", feat_dir / "feature.md")

    return tmp_project


@pytest.fixture
def project_with_epic(tmp_project: Path) -> Path:
    """Project with an epic and work stories."""
    epic_dir = tmp_project / ".ssdd" / "work" / "EPIC_001_checkout_resume"
    epic_dir.mkdir(parents=True)
    (epic_dir / "stories").mkdir()
    shutil.copy(FIXTURES_DIR / "sample_epic.md", epic_dir / "epic.md")

    story_dir = epic_dir / "stories" / "STORY_001"
    story_dir.mkdir()
    shutil.copy(FIXTURES_DIR / "sample_work_story.md", story_dir / "story.md")

    return tmp_project


class TestThemeOperations:
    def test_find_theme_dir_not_found(self, tmp_project: Path) -> None:
        state = StateManager(tmp_project)
        assert state.find_theme_dir("nonexistent") is None

    def test_find_theme_dir_by_substring(self, project_with_theme: Path) -> None:
        state = StateManager(project_with_theme)
        result = state.find_theme_dir("ecommerce")
        assert result is not None
        assert result.name == "THEME_001_ecommerce"

    def test_find_theme_dir_by_exact_name(self, project_with_theme: Path) -> None:
        state = StateManager(project_with_theme)
        result = state.find_theme_dir("THEME_001_ecommerce")
        assert result is not None
        assert result.name == "THEME_001_ecommerce"

    def test_next_theme_number_empty(self, tmp_project: Path) -> None:
        state = StateManager(tmp_project)
        assert state.next_theme_number() == 1

    def test_next_theme_number_existing(self, project_with_theme: Path) -> None:
        state = StateManager(project_with_theme)
        assert state.next_theme_number() == 2

    def test_next_feature_number_in_theme(self, project_with_theme: Path) -> None:
        state = StateManager(project_with_theme)
        theme_dir = state.find_theme_dir("ecommerce")
        assert theme_dir is not None
        assert state.next_feature_number_in_theme(theme_dir) == 2

    def test_next_feature_number_in_empty_theme(self, tmp_project: Path) -> None:
        state = StateManager(tmp_project)
        theme_dir = tmp_project / ".ssdd" / "specs" / "THEME_001_new"
        theme_dir.mkdir(parents=True)
        (theme_dir / "features").mkdir()
        assert state.next_feature_number_in_theme(theme_dir) == 1

    def test_find_feature_in_specs(self, project_with_theme: Path) -> None:
        state = StateManager(project_with_theme)
        result = state.find_feature_in_specs("checkout")
        assert result is not None
        assert result.name == "FEAT_001_checkout_resume"

    def test_find_feature_in_specs_not_found(self, project_with_theme: Path) -> None:
        state = StateManager(project_with_theme)
        result = state.find_feature_in_specs("nonexistent")
        assert result is None

    def test_list_theme_dirs(self, project_with_theme: Path) -> None:
        state = StateManager(project_with_theme)
        # Add a second theme
        (project_with_theme / ".ssdd" / "specs" / "THEME_002_auth").mkdir()
        themes = state._list_theme_dirs()
        assert len(themes) == 2
        assert themes[0].name == "THEME_001_ecommerce"
        assert themes[1].name == "THEME_002_auth"


class TestWorkStoryOperations:
    def test_find_work_story_not_found(self, tmp_project: Path) -> None:
        state = StateManager(tmp_project)
        assert state.find_work_story("nonexistent") is None

    def test_find_work_story_by_id(self, project_with_epic: Path) -> None:
        state = StateManager(project_with_epic)
        result = state.find_work_story("STORY_001")
        assert result is not None
        assert result.story_id == "STORY_001"
        assert result.epic_dir is not None
        assert "EPIC_001" in result.epic_dir.name

    def test_find_work_story_by_substring(self, project_with_epic: Path) -> None:
        state = StateManager(project_with_epic)
        result = state.find_work_story("STORY_001")
        assert result is not None
        assert result.story_path.name == "story.md"

    def test_work_story_files(self, project_with_epic: Path) -> None:
        state = StateManager(project_with_epic)
        files = state._work_story_files()
        assert len(files) == 1
        epic_dir, story_file = files[0]
        assert "EPIC_001" in epic_dir.name
        assert story_file.name == "story.md"


class TestEpicLocation:
    def test_epic_location(self) -> None:
        loc = EpicLocation(
            epic_dir=Path("/work/EPIC_001_auth"),
            epic_id="EPIC_001",
            epic_slug="EPIC_001_auth",
        )
        assert loc.epic_id == "EPIC_001"
