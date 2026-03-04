"""Tests for epic management."""

from __future__ import annotations

from pathlib import Path

from ssdd.epic_manager import EpicManager


class TestEpicManager:
    def test_next_number_empty(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        assert mgr.next_number() == 1

    def test_create_epic(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        epic_dir = mgr.create("checkout_resume")
        assert epic_dir.exists()
        assert epic_dir.name == "EPIC_001_checkout_resume"
        assert epic_dir.parent.name == "work"
        assert (epic_dir / "stories").exists()

    def test_auto_increment(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        mgr.create("first")
        mgr.create("second")
        assert mgr.next_number() == 3

    def test_find_epic_not_found(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        assert mgr.find_epic("nonexistent") is None

    def test_find_epic_by_substring(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        mgr.create("checkout_resume")
        result = mgr.find_epic("checkout")
        assert result is not None
        assert "checkout_resume" in result.name

    def test_find_epic_by_exact_name(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        epic_dir = mgr.create("auth")
        result = mgr.find_epic(epic_dir.name)
        assert result is not None
        assert result == epic_dir

    def test_scaffold_story_dir(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        epic_dir = mgr.create("auth")
        story_dir = mgr.scaffold_story_dir(epic_dir, "STORY_001")
        assert story_dir.exists()
        assert story_dir.name == "STORY_001"
        assert story_dir.parent.name == "stories"

    def test_list_epics_empty(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        assert mgr.list_epics() == []

    def test_list_epics(self, tmp_project: Path) -> None:
        mgr = EpicManager(tmp_project)
        mgr.create("auth")
        mgr.create("cart")
        epics = mgr.list_epics()
        assert len(epics) == 2
        assert epics[0].name == "EPIC_001_auth"
        assert epics[1].name == "EPIC_002_cart"

    def test_no_work_dir(self, tmp_path: Path) -> None:
        mgr = EpicManager(tmp_path)
        assert mgr.next_number() == 1
        assert mgr.find_epic("anything") is None
        assert mgr.list_epics() == []
