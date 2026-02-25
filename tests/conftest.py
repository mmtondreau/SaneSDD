"""Shared test fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with standard structure."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (tmp_path / "work").mkdir()
    (tmp_path / "design").mkdir()
    return tmp_path


@pytest.fixture
def project_with_feature(tmp_project: Path) -> Path:
    """Project with a sample feature."""
    feat_dir = tmp_project / "specs" / "FEAT_001_checkout_resume"
    feat_dir.mkdir(parents=True)
    (feat_dir / "stories").mkdir()
    shutil.copy(FIXTURES_DIR / "sample_feature.md", feat_dir / "feature.md")
    return tmp_project


@pytest.fixture
def project_with_stories(project_with_feature: Path) -> Path:
    """Project with a feature and stories."""
    stories_dir = project_with_feature / "specs" / "FEAT_001_checkout_resume" / "stories"
    shutil.copy(FIXTURES_DIR / "sample_story.md", stories_dir / "STORY_001_save_cart.md")
    shutil.copy(FIXTURES_DIR / "sample_story_002.md", stories_dir / "STORY_002_guest_checkout.md")
    return project_with_feature


@pytest.fixture
def project_with_workstream(project_with_stories: Path) -> Path:
    """Project with a feature, stories, and a workstream with tasks."""
    root = project_with_stories
    ws_feat = root / "work" / "WS_001" / "FEAT_001_checkout_resume"
    ws_feat.mkdir(parents=True)
    (ws_feat / "stories").mkdir()

    # STORY_001 tasks
    story_dir = ws_feat / "stories" / "STORY_001"
    story_dir.mkdir()
    task_001_dest = story_dir / "TASK_001_create_cart_session_table.md"
    shutil.copy(FIXTURES_DIR / "sample_task.md", task_001_dest)

    # Create TASK_002 for STORY_001 (referenced in sample_plan.yaml)
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

    # STORY_002 tasks
    story_002_dir = ws_feat / "stories" / "STORY_002"
    story_002_dir.mkdir()
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

    shutil.copy(FIXTURES_DIR / "sample_plan.yaml", ws_feat / "development_plan.yaml")

    return root
