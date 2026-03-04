---
name: sdd-feature
description: Define a new feature specification interactively. Use when the user wants to create a new feature, define requirements, or start the SDD workflow for a new piece of work.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "[description of the feature]"
---

# Phase: Feature Specification (Orchestrator)

You are the orchestrator for the Product Manager (Feature) phase. You will gather context, then dispatch a sub-agent to do the actual feature specification work.

## Pre-Checks

Before proceeding, verify the required inputs exist:

1. Check that the `specs/` directory exists by globbing for it.
If it does not exist, STOP and tell the user: "Project not initialized. Run `/sdd-init` first to create the SDD directory structure."

## Setup

Determine the next feature ID:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" next-feature-number
```

This will output a number (e.g., `1`). Use it to form the ID `FEAT_<NNN>` where NNN is zero-padded to 3 digits (e.g., `FEAT_001`). Save this as `<feature_id>`.

## Context Import

1. Check if this is an iteration on an existing feature. If the user's arguments reference an existing feature:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-feature $ARGUMENTS
```
If this succeeds, save the output as `<feature_dir>` and read prior context:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" read-context product_manager --feature <feature_dir>
```
Save any output as `PRIOR_CONTEXT`.

If find-feature fails, this is a new feature — there is no prior context.

2. For a new feature, the context export path will be determined after the feature directory is created. Pass the feature ID to the sub-agent so it can compute the path: `specs/FEAT_<NNN>_<slug>/agent/product_manager/context.md`.

For an existing feature, get the context export path:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" context-path product_manager --feature <feature_dir>
```
Save the output as `<context_export_path>`.

## Team Overrides

Check if `.roles/product_manager.md` exists. If it does, read its contents and save as `ROLE_OVERRIDES`.

## Build Sub-Agent Prompt

Read the agent prompt template: `reference/agent-prompt.md`

Read the feature template: `reference/feature-template.md`

Combine all gathered context into a single prompt for the sub-agent. The prompt must include:

1. The contents of `reference/agent-prompt.md`
2. The feature template contents (inline so the sub-agent can reference it)
3. `ROLE_OVERRIDES` (if any), prefixed with "## Team Overrides\nFollow these additional instructions:\n"
4. The feature ID and context export path as concrete values
5. `PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\nYou have been invoked before for this feature. Here is context from your previous session:\n"
6. The user's arguments: `$ARGUMENTS`

## Dispatch Sub-Agent

Use the **Task tool** to launch a sub-agent:
- `subagent_type`: `"general-purpose"`
- `description`: `"Product Manager: define feature"`
- `prompt`: The combined prompt built above

Wait for the sub-agent to complete.

## Post Sub-Agent

1. Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

2. Report the sub-agent's results to the user.

3. Display a **Files to review** section listing every file that was created or modified. Use this format:

> **Files to review:**
> - `specs/THEME_NNN_slug/theme.md`
> - `specs/THEME_NNN_slug/features/FEAT_NNN_slug/feature.md`

List the actual file paths that were generated — do not use glob patterns.

4. Tell the user:

> **Next step:** Run `/sdd-design <feature-name>` to create the high-level design for this feature.

## User Input
$ARGUMENTS
