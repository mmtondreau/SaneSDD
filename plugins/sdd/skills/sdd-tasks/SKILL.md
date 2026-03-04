---
name: sdd-tasks
description: Generate implementation tasks from stories and design documents. Use after /sdd-stories to break stories into developer tasks.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name>"
---

# Phase: Task Generation (Orchestrator)

You are the orchestrator for the Tech Lead (Tasks) phase. You will gather context, then dispatch a sub-agent to do the actual task generation work.

## Pre-Checks

Before proceeding, verify the required inputs exist:

1. Check that the feature exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-feature $ARGUMENTS
```
If this fails, STOP and tell the user: "Feature not found. Run `/sdd-feature` first to create a feature specification."

Save the output as `<feature_slug>`.

2. Check that the epic exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-epic $ARGUMENTS
```
If this fails, STOP and tell the user: "No epic found. Run `/sdd-design <feature-name>` first to create the high-level design."

Save the output as `<epic_dir>`.

3. Check that stories exist by globbing for `<epic_dir>/stories/STORY_*/story.md`.
If no stories are found, STOP and tell the user: "No stories found. Run `/sdd-stories <feature-name>` first to generate user stories."

## Approval Check

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" check-approval stories $ARGUMENTS
```

Parse the JSON output. If `approved` is `false`, display the list of unapproved artifacts and ask the user:

> **Warning:** The following artifacts from the previous step have not been approved:
> - _(list each path from the `unapproved` array)_
>
> Run `/sdd-approve stories <name>` to approve, or confirm you want to continue without approval.
> **Continue without approval?**

If the user says "no" or does not confirm, STOP. If the user says "yes" or explicitly opts in, proceed.

If `approved` is `true`, proceed silently.

## Context Import

1. Read prior agent context for the tech_lead role:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" read-context tech_lead --epic <epic_dir>
```
Save any output as `PRIOR_CONTEXT`.

2. Get the context export path:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" context-path tech_lead --epic <epic_dir>
```
Save the output as `<context_export_path>`.

## Team Overrides

Check if `.roles/tech_lead.md` exists. If it does, read its contents and save as `ROLE_OVERRIDES`.

## Build Sub-Agent Prompt

Read the agent prompt template: `reference/agent-prompt.md`

Read the task template: `reference/task-template.md`

Combine all gathered context into a single prompt for the sub-agent. The prompt must include:

1. The contents of `reference/agent-prompt.md`
2. The task template contents (inline so the sub-agent can reference it)
3. `ROLE_OVERRIDES` (if any), prefixed with "## Team Overrides\nFollow these additional instructions:\n"
4. The feature slug, epic directory path, and context export path as concrete values (replace all placeholders)
5. `PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\nYou have been invoked before for this epic. Here is context from your previous session:\n"
6. The user's arguments: `$ARGUMENTS`

## Dispatch Sub-Agent

Use the **Task tool** to launch a sub-agent:
- `subagent_type`: `"general-purpose"`
- `description`: `"Tech Lead: generate tasks"`
- `prompt`: The combined prompt built above

Wait for the sub-agent to complete.

## Post Sub-Agent

1. Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

2. Report the sub-agent's results to the user.

3. Display a **Files to review** section listing every file that was created or modified, grouped by story. Use this format:

> **Files to review:**
>
> STORY_NNN tasks:
> - `work/EPIC_NNN_slug/stories/STORY_NNN/TASK_NNN_slug.md`
> - _(list all tasks in this story)_
>
> STORY_NNN tasks:
> - _(repeat for each story)_

List the actual file paths that were generated — do not use glob patterns.

4. Tell the user:

> **Next step:** Review the files above, then run `/sdd-approve tasks <epic-name>` to approve. Then run `/sdd-plan <feature-name>` to create the execution plan.
