"""Tests for state management."""

from __future__ import annotations

from pathlib import Path

from ssdd.state import AcEntry, StateManager, Status

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestStatus:
    def test_enum_values(self) -> None:
        assert Status.TODO.value == "TODO"
        assert Status.IN_PROGRESS.value == "IN_PROGRESS"
        assert Status.DONE.value == "DONE"
        assert Status.BLOCKED.value == "BLOCKED"


class TestAcEntry:
    def test_from_dict(self) -> None:
        ac = AcEntry.from_dict({
            "id": "AC_001",
            "description": "Test criterion",
            "status": "TODO",
        })
        assert ac.id == "AC_001"
        assert ac.description == "Test criterion"
        assert ac.status == Status.TODO

    def test_to_dict(self) -> None:
        ac = AcEntry(id="AC_001", description="Test", status=Status.DONE)
        d = ac.to_dict()
        assert d == {"id": "AC_001", "description": "Test", "status": "DONE"}

    def test_default_status(self) -> None:
        ac = AcEntry.from_dict({"id": "AC_001", "description": "Test"})
        assert ac.status == Status.TODO


class TestStateManager:
    def test_load_feature(self, project_with_feature: Path) -> None:
        state = StateManager(project_with_feature)
        doc = state.read_feature("checkout_resume")
        assert doc is not None
        assert doc.id == "FEAT_001"
        assert doc.title == "Checkout Resume"
        assert doc.status == Status.TODO

    def test_find_feature_dir_by_substring(self, project_with_feature: Path) -> None:
        state = StateManager(project_with_feature)
        result = state.find_feature_dir("checkout")
        assert result is not None
        assert result.name == "FEAT_001_checkout_resume"

    def test_find_feature_dir_not_found(self, project_with_feature: Path) -> None:
        state = StateManager(project_with_feature)
        result = state.find_feature_dir("nonexistent")
        assert result is None

    def test_save_and_reload(self, project_with_feature: Path) -> None:
        state = StateManager(project_with_feature)
        doc = state.read_feature("checkout_resume")
        assert doc is not None
        doc.status = Status.IN_PROGRESS
        state.save(doc)

        reloaded = state.read_feature("checkout_resume")
        assert reloaded is not None
        assert reloaded.status == Status.IN_PROGRESS

    def test_transition(self, project_with_feature: Path) -> None:
        state = StateManager(project_with_feature)
        feat_dir = state.find_feature_dir("checkout_resume")
        assert feat_dir is not None
        path = feat_dir / "feature.md"

        doc = state.transition(path, Status.DONE)
        assert doc.status == Status.DONE

        reloaded = state.load(path)
        assert reloaded.status == Status.DONE

    def test_list_stories(self, project_with_stories: Path) -> None:
        state = StateManager(project_with_stories)
        paths = state.list_story_paths("checkout_resume")
        assert len(paths) == 2
        assert "STORY_001" in paths[0].name
        assert "STORY_002" in paths[1].name

    def test_list_story_texts(self, project_with_stories: Path) -> None:
        state = StateManager(project_with_stories)
        texts = state.list_story_texts("checkout_resume")
        assert len(texts) == 2
        assert "Save Cart" in texts[0]
        assert "Guest Checkout" in texts[1]

    def test_acceptance_criteria(self, project_with_stories: Path) -> None:
        state = StateManager(project_with_stories)
        stories = state.list_stories("checkout_resume")
        assert len(stories) == 2
        story = stories[0]
        acs = story.acceptance_criteria
        assert len(acs) == 2
        assert acs[0].id == "AC_001"
        assert acs[1].id == "AC_002"
        assert not story.all_acs_done()

    def test_all_acs_done(self, project_with_stories: Path) -> None:
        state = StateManager(project_with_stories)
        stories = state.list_stories("checkout_resume")
        story = stories[0]
        acs = story.acceptance_criteria
        for ac in acs:
            ac.status = Status.DONE
        story.acceptance_criteria = acs
        assert story.all_acs_done()

    def test_next_feature_number_empty(self, tmp_project: Path) -> None:
        state = StateManager(tmp_project)
        assert state.next_feature_number() == 1

    def test_next_feature_number_existing(self, project_with_feature: Path) -> None:
        state = StateManager(project_with_feature)
        assert state.next_feature_number() == 2

    def test_next_story_number(self, project_with_stories: Path) -> None:
        state = StateManager(project_with_stories)
        feat_dir = state.find_feature_dir("checkout_resume")
        assert feat_dir is not None
        assert state.next_story_number(feat_dir) == 3

    def test_list_task_paths(self, project_with_epic: Path) -> None:
        state = StateManager(project_with_epic)
        task_dir = (
            project_with_epic / "work" / "EPIC_001_checkout_resume"
            / "stories" / "STORY_001"
        )
        paths = state.list_task_paths(task_dir)
        assert len(paths) == 2
        assert "TASK_001" in paths[0].name
        assert "TASK_002" in paths[1].name

    def test_ac_mapping(self, project_with_epic: Path) -> None:
        state = StateManager(project_with_epic)
        task_dir = (
            project_with_epic / "work" / "EPIC_001_checkout_resume"
            / "stories" / "STORY_001"
        )
        paths = state.list_task_paths(task_dir)
        doc = state.load(paths[0])
        assert doc.ac_mapping == ["AC_001", "AC_002"]
