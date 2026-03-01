"""Thin utility CLI for SDD state operations, callable from Claude Code skills."""

from __future__ import annotations

import json
from pathlib import Path

import click

from sdd.agent_context import AgentContextManager
from sdd.config import DESIGN_DIR, SPECS_DIR, WORK_DIR, find_project_root
from sdd.index_manager import IndexManager
from sdd.plan_parser import PlanParser
from sdd.state import StateManager
from sdd.workstream import WorkstreamManager


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
@click.pass_context
def find_story(ctx: click.Context, name: str) -> None:
    """Print story location info as JSON (story_path, story_id, feature_dir, feature_slug)."""
    state = StateManager(ctx.obj["root"])
    result = state.find_story(name)
    if result:
        click.echo(json.dumps({
            "story_path": str(result.story_path),
            "story_id": result.story_id,
            "feature_dir": str(result.feature_dir),
            "feature_slug": result.feature_slug,
        }))
    else:
        raise click.ClickException(f"Story '{name}' not found")


@cli.command("find-workstream")
@click.argument("feature_name")
@click.pass_context
def find_workstream(ctx: click.Context, feature_name: str) -> None:
    """Print the active workstream feature directory path."""
    ws = WorkstreamManager(ctx.obj["root"])
    result = ws.find_active(feature_name)
    if result:
        click.echo(result)
    else:
        raise click.ClickException(f"No active workstream for '{feature_name}'")


@cli.command("create-workstream")
@click.argument("feature_slug")
@click.pass_context
def create_workstream(ctx: click.Context, feature_slug: str) -> None:
    """Create a new workstream and print its path."""
    ws = WorkstreamManager(ctx.obj["root"])
    result = ws.create(feature_slug)
    click.echo(result)


@cli.command("regenerate-index")
@click.pass_context
def regenerate_index(ctx: click.Context) -> None:
    """Regenerate INDEX.md."""
    IndexManager(ctx.obj["root"]).regenerate()
    click.echo("INDEX.md regenerated.")


@cli.command("context-path")
@click.argument("role")
@click.option("--workstream", default=None, help="Workstream feature directory path")
@click.option("--feature", default=None, help="Feature spec directory path")
def context_path(role: str, workstream: str | None, feature: str | None) -> None:
    """Print the context file path for an agent role."""
    if not workstream and not feature:
        raise click.ClickException("Provide --workstream or --feature")
    mgr = AgentContextManager()
    ws = Path(workstream) if workstream else None
    feat = Path(feature) if feature else None
    path = mgr.ensure_context_dir(role, ws_feature_dir=ws, feature_dir=feat)
    click.echo(path)


@cli.command("read-context")
@click.argument("role")
@click.option("--workstream", default=None, help="Workstream feature directory path")
@click.option("--feature", default=None, help="Feature spec directory path")
def read_context(role: str, workstream: str | None, feature: str | None) -> None:
    """Print the context file contents for an agent role, or empty if not found."""
    if not workstream and not feature:
        raise click.ClickException("Provide --workstream or --feature")
    mgr = AgentContextManager()
    ws = Path(workstream) if workstream else None
    feat = Path(feature) if feature else None
    content = mgr.read_context(role, ws_feature_dir=ws, feature_dir=feat)
    if content:
        click.echo(content, nl=False)


@cli.command("plan-json")
@click.argument("feature_name")
@click.pass_context
def plan_json(ctx: click.Context, feature_name: str) -> None:
    """Output the development plan as JSON for the implementation loop."""
    parser = PlanParser(ctx.obj["root"])
    plan = parser.load(feature_name)
    output = {
        "feature": plan.feature_name,
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
