"""Promotes completed work stories into the spec channel."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import frontmatter

from ssdd.state import StateManager


class PromotionManager:
    """Promotes completed work stories into the spec channel.

    When a work story's QA passes, the promotion step:
    1. Reads the work story and its parent epic.
    2. Determines the target theme/feature from spec_theme/spec_feature fields.
    3. Creates theme/feature directories if missing.
    4. Creates or updates the spec story (living documentation).
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._state = StateManager(project_root)

    def promote_story(self, work_story_path: Path, epic_dir: Path) -> Path:
        """Promote a completed work story into the spec channel.

        Args:
            work_story_path: Path to the work story file.
            epic_dir: Path to the parent epic directory.

        Returns:
            Path to the created/updated spec story file.

        Raises:
            ValueError: If the epic has no spec_theme or spec_feature reference.
        """
        work_story = self._state.load(work_story_path)
        epic_md = epic_dir / "epic.md"
        epic_doc = self._state.load(epic_md) if epic_md.exists() else None

        # Determine target theme/feature from epic or story metadata
        spec_theme = (
            (epic_doc.metadata.get("spec_theme") if epic_doc else None)
            or work_story.metadata.get("spec_theme")
        )
        spec_feature = (
            work_story.metadata.get("spec_feature")
            or (epic_doc.metadata.get("spec_feature") if epic_doc else None)
        )

        if not spec_theme:
            raise ValueError(
                "Cannot promote: no spec_theme on epic or work story. "
                "Set spec_theme in epic.md or the work story."
            )
        if not spec_feature:
            raise ValueError(
                "Cannot promote: no spec_feature on epic or work story. "
                "Set spec_feature in the work story or epic.md."
            )

        theme_title = spec_theme.replace("_", " ").title()
        theme_dir = self._ensure_theme(spec_theme, theme_title)

        feature_title = spec_feature.replace("_", " ").title()
        feature_dir = self._ensure_feature(theme_dir, spec_feature, feature_title)

        return self._create_spec_story(feature_dir, work_story)

    def _ensure_theme(self, theme_id: str, title: str) -> Path:
        """Create theme directory and theme.md if they don't exist."""
        theme_dir = self._state.find_theme_dir(theme_id)
        if theme_dir:
            return theme_dir

        # Create new theme directory
        slug = theme_id.lower().replace(" ", "_")
        if not slug.startswith("THEME_"):
            slug = theme_id
        theme_dir = self._root / "specs" / slug
        theme_dir.mkdir(parents=True, exist_ok=True)
        (theme_dir / "features").mkdir(exist_ok=True)

        # Write theme.md
        today = date.today().isoformat()
        post = frontmatter.Post(
            f"# {title}\n",
            id=theme_id,
            title=title,
            status="IN_PROGRESS",
            created=today,
            updated=today,
        )
        theme_md = theme_dir / "theme.md"
        with open(theme_md, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        return theme_dir

    def _ensure_feature(self, theme_dir: Path, feat_id: str, title: str) -> Path:
        """Create feature directory and feature.md under a theme if they don't exist."""
        features_dir = theme_dir / "features"
        features_dir.mkdir(exist_ok=True)

        # Check if feature already exists
        for d in features_dir.iterdir():
            if d.is_dir() and (d.name == feat_id or feat_id in d.name):
                return d

        # Create new feature directory
        slug = feat_id.lower().replace(" ", "_")
        if not slug.startswith("FEAT_"):
            slug = feat_id
        feat_dir = features_dir / slug
        feat_dir.mkdir(parents=True, exist_ok=True)
        (feat_dir / "stories").mkdir(exist_ok=True)

        # Determine theme ID from theme.md
        theme_md = theme_dir / "theme.md"
        theme_id = ""
        if theme_md.exists():
            theme_doc = self._state.load(theme_md)
            theme_id = theme_doc.id

        # Write feature.md
        today = date.today().isoformat()
        post = frontmatter.Post(
            f"# {title}\n",
            id=feat_id,
            title=title,
            status="IN_PROGRESS",
            theme=theme_id,
            created=today,
            updated=today,
        )
        feature_md = feat_dir / "feature.md"
        with open(feature_md, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        return feat_dir

    def _create_spec_story(self, feature_dir: Path, work_story: "frontmatter.Post") -> Path:
        """Transform a work story into a spec story (living documentation).

        Strips ACs (which are an execution concern) and converts the story
        body into a description of the current system state.
        """
        stories_dir = feature_dir / "stories"
        stories_dir.mkdir(exist_ok=True)

        story_id = work_story.id
        story_slug = work_story.path.parent.name if work_story.path else story_id
        # Use the story directory name as slug basis
        spec_story_name = f"{story_slug}.md" if story_slug.startswith("STORY_") else f"{story_id}.md"
        spec_story_path = stories_dir / spec_story_name

        # Determine feature ID from feature.md
        feature_md = feature_dir / "feature.md"
        feature_id = ""
        if feature_md.exists():
            feat_doc = self._state.load(feature_md)
            feature_id = feat_doc.id

        today = date.today().isoformat()
        post = frontmatter.Post(
            work_story.content,
            id=story_id,
            title=work_story.title,
            status="DONE",
            feature=feature_id,
            created=work_story.metadata.get("created", today),
            updated=today,
        )
        with open(spec_story_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        return spec_story_path
