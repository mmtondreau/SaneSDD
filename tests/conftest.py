"""Shared test fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with standard structure."""
    ssdd = tmp_path / ".ssdd"
    ssdd.mkdir()
    specs = ssdd / "specs"
    specs.mkdir()
    (ssdd / "work").mkdir()
    (ssdd / "design").mkdir()
    return tmp_path


@pytest.fixture
def project_with_feature(tmp_project: Path) -> Path:
    """Project with a sample feature."""
    feat_dir = tmp_project / ".ssdd" / "specs" / "FEAT_001_checkout_resume"
    feat_dir.mkdir(parents=True)
    (feat_dir / "stories").mkdir()
    shutil.copy(FIXTURES_DIR / "sample_feature.md", feat_dir / "feature.md")
    return tmp_project


@pytest.fixture
def project_with_stories(project_with_feature: Path) -> Path:
    """Project with a feature and stories."""
    stories_dir = project_with_feature / ".ssdd" / "specs" / "FEAT_001_checkout_resume" / "stories"
    shutil.copy(FIXTURES_DIR / "sample_story.md", stories_dir / "STORY_001_save_cart.md")
    shutil.copy(FIXTURES_DIR / "sample_story_002.md", stories_dir / "STORY_002_guest_checkout.md")
    return project_with_feature


@pytest.fixture
def project_with_epic(project_with_stories: Path) -> Path:
    """Project with a feature, stories, and an epic with tasks."""
    root = project_with_stories
    epic_dir = root / ".ssdd" / "work" / "EPIC_001_checkout_resume"
    epic_dir.mkdir(parents=True)
    (epic_dir / "stories").mkdir()
    shutil.copy(FIXTURES_DIR / "sample_epic.md", epic_dir / "epic.md")

    # STORY_001 with work story + tasks
    story_dir = epic_dir / "stories" / "STORY_001"
    story_dir.mkdir()
    shutil.copy(FIXTURES_DIR / "sample_work_story.md", story_dir / "story.md")
    task_001_dest = story_dir / "TASK_001_create_cart_session_table.md"
    shutil.copy(FIXTURES_DIR / "sample_task.md", task_001_dest)

    task_002_content = """\
---
id: "TASK_002"
title: "Add Merge Endpoint"
status: "TODO"
story: "STORY_001"
depends_on: ["TASK_001"]
ac_mapping:
  - "AC_002"
created: "2026-02-23"
updated: "2026-02-23"
---

## Description
Add API endpoint to merge guest cart with authenticated cart.
"""
    (story_dir / "TASK_002_add_merge_endpoint.md").write_text(task_002_content)

    # STORY_002 with work story + tasks
    story_002_dir = epic_dir / "stories" / "STORY_002"
    story_002_dir.mkdir()

    story_002_content = """\
---
id: "STORY_002"
title: "Guest Checkout"
status: "TODO"
epic: "EPIC_001"
depends_on: []
acceptance_criteria:
  - id: "AC_003"
    description: "Guest users can checkout without account"
    status: "TODO"
created: "2026-02-23"
updated: "2026-02-23"
---

## User Story
As a guest, I want to checkout without creating an account.
"""
    (story_002_dir / "story.md").write_text(story_002_content)

    task_001_s2_content = """\
---
id: "TASK_001"
title: "Allow Guest Checkout"
status: "TODO"
story: "STORY_002"
depends_on: []
ac_mapping:
  - "AC_003"
created: "2026-02-23"
updated: "2026-02-23"
---

## Description
Allow guest users to checkout without creating an account.
"""
    (story_002_dir / "TASK_001_allow_guest_checkout.md").write_text(task_001_s2_content)

    # Create development plan (epic-format)
    plan_content = """\
epic: "EPIC_001_checkout_resume"
generated_at: "2026-02-23T10:00:00"
stories:
  - story_id: "STORY_001"
    order: 1
    tasks:
      - task_id: "TASK_001"
        order: 1
        depends_on: []
        estimated_effort: "medium"
      - task_id: "TASK_002"
        order: 2
        depends_on: ["TASK_001"]
        estimated_effort: "small"
  - story_id: "STORY_002"
    order: 2
    tasks:
      - task_id: "TASK_001"
        order: 1
        depends_on: []
        estimated_effort: "large"
risks:
  - description: "Cart merge logic may be complex"
    severity: "medium"
    mitigation: "Start with simple last-write-wins strategy"
"""
    (epic_dir / "development_plan.yaml").write_text(plan_content)

    return root
