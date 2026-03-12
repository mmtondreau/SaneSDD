"""Generate 'Files to review' output for SaneSDD skills."""

from __future__ import annotations

from pathlib import Path

from ssdd.config import DESIGN_DIR
from ssdd.design_manager import DesignManager
from ssdd.epic_manager import EpicManager
from ssdd.state import StateManager


STEPS = ("feature", "design", "stories", "tasks", "plan", "implement", "init")


class FilesToReviewGenerator:
    """Generates markdown-formatted 'Files to review' output."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._state = StateManager(project_root)
        self._epics = EpicManager(project_root)
        self._design_mgr = DesignManager(project_root)

    def generate(
        self,
        step: str,
        name: str = "",
        promoted_stories: list[str] | None = None,
    ) -> str:
        """Dispatch to the step-specific method and return markdown."""
        method = getattr(self, f"_{step}", None)
        if not method:
            return f"Unknown step: {step}"
        if step == "implement":
            return method(name, promoted_stories or [])
        if step == "init":
            return method()
        return method(name)

    # ── Helpers ────────────────────────────────────────────────────

    def _rel(self, path: Path) -> str:
        """Convert an absolute path to a project-root-relative string."""
        try:
            return str(path.resolve().relative_to(self._root.resolve()))
        except ValueError:
            return str(path)

    def _link(self, path: Path) -> str:
        """Format a clickable markdown link: [filename](relative_path)."""
        rel = self._rel(path)
        return f"[{path.name}]({rel})"

    def _format_group(self, title: str, paths: list[Path]) -> str:
        """Format a titled group of file links."""
        if not paths:
            return ""
        lines = [f"{title}:"]
        for p in paths:
            lines.append(f"- {self._link(p)}")
        return "\n".join(lines)

    def _ssdd_rel(self, path: Path) -> str:
        """Convert an absolute path to a .ssdd/-relative string for approve commands."""
        rel = self._rel(path)
        if rel.startswith(".ssdd/"):
            return rel[len(".ssdd/"):]
        return rel

    # ── Step implementations ───────────────────────────────────────

    def _feature(self, name: str) -> str:
        feat_dir = self._state.find_feature_dir(name)
        if not feat_dir:
            return f"Feature '{name}' not found."

        files: list[Path] = []
        # Theme file (parent of features/ dir)
        theme_dir = feat_dir.parent.parent
        theme_md = theme_dir / "theme.md"
        if theme_md.exists():
            files.append(theme_md)
        # Feature file
        feature_md = feat_dir / "feature.md"
        if feature_md.exists():
            files.append(feature_md)

        if not files:
            return "No files found to review."

        lines = ["**Files to review:**", ""]
        for f in files:
            lines.append(f"- {self._link(f)}")

        approve_path = self._ssdd_rel(feature_md) if feature_md.exists() else ""
        lines.append("")
        lines.append(
            f"**Next step:** Review the files above, then approve by running "
            f"`/ssdd-approve {approve_path}`. "
            f"Then run `/ssdd-design {name}` to create the high-level design."
        )
        return "\n".join(lines)

    def _design(self, name: str) -> str:
        epic_dir = self._epics.find_epic(name)
        if not epic_dir:
            return f"Epic '{name}' not found."

        sections: list[str] = []

        # Epic files
        epic_files: list[Path] = []
        for fname in ("epic.md", "high_level_design.md"):
            p = epic_dir / fname
            if p.exists():
                epic_files.append(p)
        if epic_files:
            sections.append(self._format_group("Epic", epic_files))

        # System architecture
        design_md = self._root / DESIGN_DIR / "design.md"
        if design_md.exists():
            sections.append(self._format_group("System architecture", [design_md]))

        # Domains
        domain_files = [
            d / "domain.md" for d in self._design_mgr.list_domains()
            if (d / "domain.md").exists()
        ]
        if domain_files:
            sections.append(self._format_group("Domains", domain_files))

        # Components
        comp_files = self._design_mgr.list_components()
        if comp_files:
            sections.append(self._format_group("Components", comp_files))

        if not sections:
            return "No files found to review."

        hld = epic_dir / "high_level_design.md"
        approve_path = self._ssdd_rel(hld) if hld.exists() else ""
        lines = ["**Files to review:**", ""]
        lines.append("\n\n".join(sections))
        lines.append("")
        lines.append(
            f"**Next step:** Review the files above, then approve by running "
            f"`/ssdd-approve {approve_path}`. "
            f"Then run `/ssdd-stories {name}` to generate user stories."
        )
        return "\n".join(lines)

    def _stories(self, name: str) -> str:
        epic_dir = self._epics.find_epic(name)
        if not epic_dir:
            return f"Epic '{name}' not found."

        stories_dir = epic_dir / "stories"
        if not stories_dir.exists():
            return "No stories directory found."

        story_files: list[Path] = []
        for story_dir in sorted(stories_dir.iterdir()):
            if story_dir.is_dir() and story_dir.name.startswith("STORY_"):
                story_md = story_dir / "story.md"
                if story_md.exists():
                    story_files.append(story_md)

        if not story_files:
            return "No story files found."

        approve_path = self._ssdd_rel(stories_dir)
        lines = ["**Files to review:**", ""]
        lines.append(self._format_group("Stories", story_files))
        lines.append("")
        lines.append(
            f"**Next step:** Review the files above, then approve all stories: "
            f"`/ssdd-approve {approve_path}`. "
            f"Then run `/ssdd-tasks {name}` to generate implementation tasks."
        )
        return "\n".join(lines)

    def _tasks(self, name: str) -> str:
        epic_dir = self._epics.find_epic(name)
        if not epic_dir:
            return f"Epic '{name}' not found."

        stories_dir = epic_dir / "stories"
        if not stories_dir.exists():
            return "No stories directory found."

        sections: list[str] = []
        for story_dir in sorted(stories_dir.iterdir()):
            if not story_dir.is_dir() or not story_dir.name.startswith("STORY_"):
                continue
            task_files = sorted(story_dir.glob("TASK_*.md"))
            if task_files:
                sections.append(
                    self._format_group(f"{story_dir.name} tasks", task_files)
                )

        if not sections:
            return "No task files found."

        approve_path = self._ssdd_rel(stories_dir)
        lines = ["**Files to review:**", ""]
        lines.append("\n\n".join(sections))
        lines.append("")
        lines.append(
            f"**Next step:** Review the files above, then approve all tasks: "
            f"`/ssdd-approve {approve_path}`. "
            f"Then run `/ssdd-plan {name}` to create the execution plan."
        )
        return "\n".join(lines)

    def _plan(self, name: str) -> str:
        epic_dir = self._epics.find_epic(name)
        if not epic_dir:
            return f"Epic '{name}' not found."

        plan_path = epic_dir / "development_plan.yaml"
        if not plan_path.exists():
            return "No development_plan.yaml found."

        approve_path = self._ssdd_rel(plan_path)
        lines = ["**Files to review:**", ""]
        lines.append(f"- {self._link(plan_path)}")
        lines.append("")
        lines.append(
            f"**Next step:** Review the file above, then approve by running "
            f"`/ssdd-approve {approve_path}`. "
            f"Then run `/ssdd-implement <story-id>` to start implementing. "
            f"Stories should be implemented in plan order."
        )
        return "\n".join(lines)

    def _find_story_dir(self, name: str) -> Path | None:
        """Find a story directory by name across all epics, or fall back to
        finding the first story in an epic matched by name."""
        for epic_dir in self._epics.list_epics():
            stories_dir = epic_dir / "stories"
            if not stories_dir.exists():
                continue
            for d in sorted(stories_dir.iterdir()):
                if d.is_dir() and d.name.startswith("STORY_") and name in d.name:
                    return d
        # Fall back: treat name as epic name, return first story
        epic_dir = self._epics.find_epic(name)
        if epic_dir:
            return self._first_story_dir(epic_dir / "stories")
        return None

    def _first_story_dir(self, stories_dir: Path) -> Path | None:
        """Return the first STORY_* directory under stories_dir."""
        if not stories_dir.exists():
            return None
        for d in sorted(stories_dir.iterdir()):
            if d.is_dir() and d.name.startswith("STORY_"):
                return d
        return None

    def _collect_story_files(self, story_dir: Path) -> list[Path]:
        """Collect story.md and all TASK_*.md files from a story directory."""
        files: list[Path] = []
        story_md = story_dir / "story.md"
        if story_md.exists():
            files.append(story_md)
        files.extend(sorted(story_dir.glob("TASK_*.md")))
        return files

    def _is_story_done(self, story_dir: Path) -> bool:
        """Check if the story.md in a directory has status DONE."""
        story_md = story_dir / "story.md"
        if not story_md.exists():
            return False
        doc = self._state.load(story_md)
        return doc.metadata.get("status", "").upper() == "DONE"

    def _implement(self, name: str, promoted_stories: list[str]) -> str:
        story_dir = self._find_story_dir(name)

        sections: list[str] = []

        if story_dir:
            updated = self._collect_story_files(story_dir)
            if updated:
                sections.append(
                    self._format_group("Updated stories and tasks", updated)
                )

        if promoted_stories:
            promoted_paths = [Path(p) for p in promoted_stories]
            sections.append(
                self._format_group("Promoted spec stories", promoted_paths)
            )

        if not sections:
            return "No files found to review."

        is_done = story_dir is not None and self._is_story_done(story_dir)

        lines = ["**Files to review:**", ""]
        lines.append("\n\n".join(sections))
        lines.append("")

        if is_done:
            lines.append(
                f"**Story complete!** Run `/ssdd-merge {name}` to merge "
                f"the story branch to main."
            )
        else:
            lines.append(
                f"**Story incomplete.** Review the blocked tasks above, "
                f"then re-run `/ssdd-implement {name}` to continue."
            )
        return "\n".join(lines)

    def _init(self) -> str:
        sections: list[str] = []

        # System architecture
        design_md = self._root / DESIGN_DIR / "design.md"
        if design_md.exists():
            sections.append(self._format_group("System architecture", [design_md]))

        # Domains
        domain_files = [
            d / "domain.md" for d in self._design_mgr.list_domains()
            if (d / "domain.md").exists()
        ]
        if domain_files:
            sections.append(self._format_group("Domains", domain_files))

        # Components
        comp_files = self._design_mgr.list_components()
        if comp_files:
            sections.append(self._format_group("Components", comp_files))

        if not sections:
            return ""

        lines = ["**Files to review:**", ""]
        lines.append("\n\n".join(sections))
        lines.append("")
        lines.append(
            "Review these files for accuracy before proceeding. "
            "Domains define your system's bounded contexts; components detail "
            "the internal structure. Use `/ssdd-feature` to define your next feature."
        )
        return "\n".join(lines)
