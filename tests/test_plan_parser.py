"""Tests for plan parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdd.epic_manager import EpicManager
from sdd.plan_parser import PlanParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPlanParser:
    def test_load_plan(self, project_with_epic: Path) -> None:
        parser = PlanParser(project_with_epic)
        plan = parser.load("checkout_resume")
        assert plan.epic_name == "EPIC_001_checkout_resume"
        assert len(plan.stories) == 2

    def test_story_ordering(self, project_with_epic: Path) -> None:
        parser = PlanParser(project_with_epic)
        plan = parser.load("checkout_resume")
        assert plan.stories[0].story_id == "STORY_001"
        assert plan.stories[0].order == 1
        assert plan.stories[1].story_id == "STORY_002"
        assert plan.stories[1].order == 2

    def test_task_ordering(self, project_with_epic: Path) -> None:
        parser = PlanParser(project_with_epic)
        plan = parser.load("checkout_resume")
        story1 = plan.stories[0]
        assert len(story1.tasks) == 2
        assert story1.tasks[0].task_id == "TASK_001"
        assert story1.tasks[1].task_id == "TASK_002"

    def test_task_path_resolved(self, project_with_epic: Path) -> None:
        parser = PlanParser(project_with_epic)
        plan = parser.load("checkout_resume")
        task = plan.stories[0].tasks[0]
        assert task.task_path.exists()
        assert "TASK_001" in task.task_path.name

    def test_no_epic_raises(self, tmp_project: Path) -> None:
        parser = PlanParser(tmp_project)
        with pytest.raises(FileNotFoundError, match="No epic found"):
            parser.load("nonexistent")

    def test_no_plan_raises(self, project_with_feature: Path) -> None:
        mgr = EpicManager(project_with_feature)
        mgr.create("checkout_resume")

        parser = PlanParser(project_with_feature)
        with pytest.raises(FileNotFoundError, match="No development plan"):
            parser.load("checkout_resume")
