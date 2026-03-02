"""Tests for story promotion from work to spec channel."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from sdd.promotion_manager import PromotionManager
from sdd.state import StateManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def project_for_promotion(tmp_project: Path) -> Path:
    """Project with an epic containing a completed work story."""
    # Create epic with spec_theme and spec_feature references
    epic_dir = tmp_project / "work" / "EPIC_001_checkout_resume"
    epic_dir.mkdir(parents=True)
    (epic_dir / "stories").mkdir()
    shutil.copy(FIXTURES_DIR / "sample_epic.md", epic_dir / "epic.md")

    # Create completed work story
    story_dir = epic_dir / "stories" / "STORY_001"
    story_dir.mkdir()
    shutil.copy(FIXTURES_DIR / "sample_work_story.md", story_dir / "story.md")

    return tmp_project


class TestPromotionManager:
    def test_promote_story_creates_theme(self, project_for_promotion: Path) -> None:
        mgr = PromotionManager(project_for_promotion)
        epic_dir = project_for_promotion / "work" / "EPIC_001_checkout_resume"
        story_path = epic_dir / "stories" / "STORY_001" / "story.md"

        spec_path = mgr.promote_story(story_path, epic_dir)

        assert spec_path.exists()
        # Theme should have been created
        specs_dir = project_for_promotion / "specs"
        theme_dirs = [d for d in specs_dir.iterdir() if d.is_dir() and "THEME" in d.name]
        assert len(theme_dirs) == 1

    def test_promote_story_creates_feature(self, project_for_promotion: Path) -> None:
        mgr = PromotionManager(project_for_promotion)
        epic_dir = project_for_promotion / "work" / "EPIC_001_checkout_resume"
        story_path = epic_dir / "stories" / "STORY_001" / "story.md"

        spec_path = mgr.promote_story(story_path, epic_dir)

        # Feature should exist under the theme
        state = StateManager(project_for_promotion)
        feat_dir = state.find_feature_in_specs("FEAT_001")
        assert feat_dir is not None
        assert (feat_dir / "feature.md").exists()

    def test_promote_story_creates_spec_story(self, project_for_promotion: Path) -> None:
        mgr = PromotionManager(project_for_promotion)
        epic_dir = project_for_promotion / "work" / "EPIC_001_checkout_resume"
        story_path = epic_dir / "stories" / "STORY_001" / "story.md"

        spec_path = mgr.promote_story(story_path, epic_dir)

        assert spec_path.exists()
        state = StateManager(project_for_promotion)
        doc = state.load(spec_path)
        assert doc.id == "STORY_001"
        assert doc.title == "Save Cart"
        assert doc.status.value == "DONE"
        # Spec story should not have acceptance_criteria
        assert "acceptance_criteria" not in doc.metadata

    def test_promote_story_uses_existing_theme(self, project_for_promotion: Path) -> None:
        root = project_for_promotion
        # Pre-create the theme
        theme_dir = root / "specs" / "THEME_001"
        theme_dir.mkdir(parents=True)
        (theme_dir / "features").mkdir()
        shutil.copy(FIXTURES_DIR / "sample_theme.md", theme_dir / "theme.md")

        mgr = PromotionManager(root)
        epic_dir = root / "work" / "EPIC_001_checkout_resume"
        story_path = epic_dir / "stories" / "STORY_001" / "story.md"

        spec_path = mgr.promote_story(story_path, epic_dir)

        assert spec_path.exists()
        # Should still be just one theme
        theme_dirs = [
            d for d in (root / "specs").iterdir()
            if d.is_dir() and "THEME" in d.name
        ]
        assert len(theme_dirs) == 1

    def test_promote_story_no_theme_raises(self, tmp_project: Path) -> None:
        """Promote fails if no spec_theme is set."""
        # Create epic without spec_theme
        epic_dir = tmp_project / "work" / "EPIC_001_test"
        epic_dir.mkdir(parents=True)
        (epic_dir / "stories" / "STORY_001").mkdir(parents=True)

        epic_content = """\
---
id: "EPIC_001"
title: "Test"
status: "TODO"
created: "2026-02-28"
updated: "2026-02-28"
---

# Test
"""
        (epic_dir / "epic.md").write_text(epic_content)

        story_content = """\
---
id: "STORY_001"
title: "Test Story"
status: "DONE"
epic: "EPIC_001"
depends_on: []
created: "2026-02-28"
updated: "2026-02-28"
---

## User Story
Test story content.
"""
        story_path = epic_dir / "stories" / "STORY_001" / "story.md"
        story_path.write_text(story_content)

        mgr = PromotionManager(tmp_project)
        with pytest.raises(ValueError, match="spec_theme"):
            mgr.promote_story(story_path, epic_dir)

    def test_promote_story_no_feature_raises(self, tmp_project: Path) -> None:
        """Promote fails if no spec_feature is set."""
        epic_dir = tmp_project / "work" / "EPIC_001_test"
        epic_dir.mkdir(parents=True)
        (epic_dir / "stories" / "STORY_001").mkdir(parents=True)

        epic_content = """\
---
id: "EPIC_001"
title: "Test"
status: "TODO"
spec_theme: "THEME_001"
created: "2026-02-28"
updated: "2026-02-28"
---

# Test
"""
        (epic_dir / "epic.md").write_text(epic_content)

        story_content = """\
---
id: "STORY_001"
title: "Test Story"
status: "DONE"
epic: "EPIC_001"
depends_on: []
created: "2026-02-28"
updated: "2026-02-28"
---

## User Story
Test story content.
"""
        story_path = epic_dir / "stories" / "STORY_001" / "story.md"
        story_path.write_text(story_content)

        mgr = PromotionManager(tmp_project)
        with pytest.raises(ValueError, match="spec_feature"):
            mgr.promote_story(story_path, epic_dir)
