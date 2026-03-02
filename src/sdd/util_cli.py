"""Thin utility CLI for SDD state operations, callable from Claude Code skills."""

from __future__ import annotations

import json
from pathlib import Path

import click

from sdd.agent_context import AgentContextManager
from sdd.config import DESIGN_DIR, SPECS_DIR, WORK_DIR, find_project_root
from sdd.design_manager import DesignManager
from sdd.epic_manager import EpicManager
from sdd.index_manager import IndexManager
from sdd.plan_parser import PlanParser
from sdd.promotion_manager import PromotionManager
from sdd.state import StateManager


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """SDD utility commands for state operations."""
    ctx.ensure_object(dict)
    ctx.obj["root"] = find_project_root()


@cli.command("init")
@click.option(
    "--path", default=".", type=click.Path(),
    help="Directory to initialize (defaults to current directory)",
)
def init(path: str) -> None:
    """Initialize a new SDD project with specs/, work/, design/ directories."""
    root = Path(path).resolve()

    created: list[str] = []
    for dirname in (SPECS_DIR, WORK_DIR, DESIGN_DIR):
        target = root / dirname
        if not target.exists():
            target.mkdir(parents=True)
            created.append(dirname)

    if created:
        click.echo(f"Initialized SDD project in {root}")
        for d in created:
            click.echo(f"  created {d}/")
    else:
        click.echo(f"SDD project already initialized in {root}")

    IndexManager(root).regenerate()
    click.echo("INDEX.md regenerated.")


@cli.command("next-feature-number")
@click.pass_context
def next_feature_number(ctx: click.Context) -> None:
    """Print the next available feature number."""
    state = StateManager(ctx.obj["root"])
    click.echo(state.next_feature_number())


@cli.command("next-story-number")
@click.argument("feature_dir")
@click.pass_context
def next_story_number(ctx: click.Context, feature_dir: str) -> None:
    """Print the next available story number for a feature directory."""
    state = StateManager(ctx.obj["root"])
    click.echo(state.next_story_number(Path(feature_dir)))


@cli.command("next-task-number")
@click.argument("ws_story_dir")
@click.pass_context
def next_task_number(ctx: click.Context, ws_story_dir: str) -> None:
    """Print the next available task number for a workstream story directory."""
    state = StateManager(ctx.obj["root"])
    click.echo(state.next_task_number(Path(ws_story_dir)))


@cli.command("find-feature")
@click.argument("name")
@click.pass_context
def find_feature(ctx: click.Context, name: str) -> None:
    """Print the feature directory path for a given name/substring."""
    state = StateManager(ctx.obj["root"])
    result = state.find_feature_dir(name)
    if result:
        click.echo(result)
    else:
        raise click.ClickException(f"Feature '{name}' not found")


@cli.command("find-story")
@click.argument("name")
@click.option(
    "--channel", default="both", type=click.Choice(["spec", "work", "both"]),
    help="Search spec channel, work channel, or both (default: both)",
)
@click.pass_context
def find_story(ctx: click.Context, name: str, channel: str) -> None:
    """Print story location info as JSON."""
    state = StateManager(ctx.obj["root"])
    result = state.find_story(name, channel=channel)
    if result:
        data: dict[str, str | None] = {
            "story_path": str(result.story_path),
            "story_id": result.story_id,
            "feature_dir": str(result.feature_dir),
            "feature_slug": result.feature_slug,
        }
        if result.epic_dir:
            data["epic_dir"] = str(result.epic_dir)
            data["epic_slug"] = result.epic_slug
        click.echo(json.dumps(data))
    else:
        raise click.ClickException(f"Story '{name}' not found")



@cli.command("regenerate-index")
@click.pass_context
def regenerate_index(ctx: click.Context) -> None:
    """Regenerate INDEX.md."""
    IndexManager(ctx.obj["root"]).regenerate()
    click.echo("INDEX.md regenerated.")


@cli.command("context-path")
@click.argument("role")
@click.option("--epic", default=None, help="Epic directory path")
@click.option("--theme", default=None, help="Theme spec directory path")
@click.option("--workstream", default=None, help="Legacy: workstream feature directory path")
@click.option("--feature", default=None, help="Legacy: feature spec directory path")
def context_path(
    role: str,
    epic: str | None,
    theme: str | None,
    workstream: str | None,
    feature: str | None,
) -> None:
    """Print the context file path for an agent role."""
    if not any([epic, theme, workstream, feature]):
        raise click.ClickException("Provide --epic, --theme, --workstream, or --feature")
    mgr = AgentContextManager()
    path = mgr.ensure_context_dir(
        role,
        epic_dir=Path(epic) if epic else None,
        theme_dir=Path(theme) if theme else None,
        ws_feature_dir=Path(workstream) if workstream else None,
        feature_dir=Path(feature) if feature else None,
    )
    click.echo(path)


@cli.command("read-context")
@click.argument("role")
@click.option("--epic", default=None, help="Epic directory path")
@click.option("--theme", default=None, help="Theme spec directory path")
@click.option("--workstream", default=None, help="Legacy: workstream feature directory path")
@click.option("--feature", default=None, help="Legacy: feature spec directory path")
def read_context(
    role: str,
    epic: str | None,
    theme: str | None,
    workstream: str | None,
    feature: str | None,
) -> None:
    """Print the context file contents for an agent role, or empty if not found."""
    if not any([epic, theme, workstream, feature]):
        raise click.ClickException("Provide --epic, --theme, --workstream, or --feature")
    mgr = AgentContextManager()
    content = mgr.read_context(
        role,
        epic_dir=Path(epic) if epic else None,
        theme_dir=Path(theme) if theme else None,
        ws_feature_dir=Path(workstream) if workstream else None,
        feature_dir=Path(feature) if feature else None,
    )
    if content:
        click.echo(content, nl=False)


@cli.command("plan-json")
@click.argument("epic_name")
@click.pass_context
def plan_json(ctx: click.Context, epic_name: str) -> None:
    """Output the development plan as JSON for the implementation loop."""
    parser = PlanParser(ctx.obj["root"])
    plan = parser.load(epic_name)
    output = {
        "epic": plan.epic_name,
        "stories": [
            {
                "story_id": s.story_id,
                "story_path": str(s.story_path),
                "order": s.order,
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "task_path": str(t.task_path),
                        "order": t.order,
                    }
                    for t in s.tasks
                ],
            }
            for s in plan.stories
        ],
    }
    click.echo(json.dumps(output, indent=2))


# ── Theme commands ────────────────────────────────────────────────


@cli.command("next-theme-number")
@click.pass_context
def next_theme_number(ctx: click.Context) -> None:
    """Print the next available theme number."""
    state = StateManager(ctx.obj["root"])
    click.echo(state.next_theme_number())


@cli.command("find-theme")
@click.argument("name")
@click.pass_context
def find_theme(ctx: click.Context, name: str) -> None:
    """Print the theme directory path for a given name/substring."""
    state = StateManager(ctx.obj["root"])
    result = state.find_theme_dir(name)
    if result:
        click.echo(result)
    else:
        raise click.ClickException(f"Theme '{name}' not found")


@cli.command("next-feature-number-in-theme")
@click.argument("theme_dir")
@click.pass_context
def next_feature_number_in_theme(ctx: click.Context, theme_dir: str) -> None:
    """Print the next available feature number within a theme."""
    state = StateManager(ctx.obj["root"])
    click.echo(state.next_feature_number_in_theme(Path(theme_dir)))


# ── Epic commands ─────────────────────────────────────────────────


@cli.command("next-epic-number")
@click.pass_context
def next_epic_number(ctx: click.Context) -> None:
    """Print the next available epic number."""
    mgr = EpicManager(ctx.obj["root"])
    click.echo(mgr.next_number())


@cli.command("find-epic")
@click.argument("name")
@click.pass_context
def find_epic(ctx: click.Context, name: str) -> None:
    """Print the epic directory path for a given name/substring."""
    mgr = EpicManager(ctx.obj["root"])
    result = mgr.find_epic(name)
    if result:
        click.echo(result)
    else:
        raise click.ClickException(f"Epic '{name}' not found")


@cli.command("create-epic")
@click.argument("epic_slug")
@click.pass_context
def create_epic(ctx: click.Context, epic_slug: str) -> None:
    """Create a new epic and print its path."""
    mgr = EpicManager(ctx.obj["root"])
    result = mgr.create(epic_slug)
    click.echo(result)


# ── Domain commands ───────────────────────────────────────────────


@cli.command("next-domain-number")
@click.pass_context
def next_domain_number(ctx: click.Context) -> None:
    """Print the next available domain number."""
    mgr = DesignManager(ctx.obj["root"])
    click.echo(mgr.next_domain_number())


@cli.command("find-domain")
@click.argument("name")
@click.pass_context
def find_domain(ctx: click.Context, name: str) -> None:
    """Print the domain directory path for a given name/substring."""
    mgr = DesignManager(ctx.obj["root"])
    result = mgr.find_domain(name)
    if result:
        click.echo(result)
    else:
        raise click.ClickException(f"Domain '{name}' not found")


# ── Promotion commands ────────────────────────────────────────────


@cli.command("promote-story")
@click.argument("work_story_path")
@click.option("--epic", required=True, help="Epic directory path")
@click.pass_context
def promote_story(ctx: click.Context, work_story_path: str, epic: str) -> None:
    """Promote a completed work story into the spec channel."""
    mgr = PromotionManager(ctx.obj["root"])
    result = mgr.promote_story(Path(work_story_path), Path(epic))
    click.echo(result)
