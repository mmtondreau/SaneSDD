---
name: sdd-design
description: Create a high-level design for a feature. Use after a feature spec has been created with /sdd-feature.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name>"
---

# Phase: High-Level Design (Orchestrator)

You are the orchestrator for the System Architect phase. You will gather context, then dispatch a sub-agent to do the actual design work.

## Pre-Checks

Before proceeding, verify the required inputs exist:

1. Check that the feature exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-feature $ARGUMENTS
```
If this fails, STOP and tell the user: "Feature not found. Run `/sdd-feature` first to create a feature specification."

Save the output as `<feature_slug>` (e.g., `FEAT_001_checkout_resume`).

## Setup

Create a workstream:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" create-workstream <feature_slug>
```

Save the output as `<ws_feature_dir>`.

## Context Import

1. Read prior agent context:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" read-context system_architect --workstream <ws_feature_dir>
```
Save any output as `PRIOR_CONTEXT`. If empty, there is no prior context.

2. Get the context export path:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" context-path system_architect --workstream <ws_feature_dir>
```
Save the output as `<context_export_path>`.

3. Check for cross-role context from the Product Manager (feature definition phase):
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" read-context product_manager --feature <feature_dir>
```
Where `<feature_dir>` is `specs/<feature_slug>`. Save any output as `PM_CONTEXT`.

## Team Overrides

Check if `.roles/system_architect.md` exists. If it does, read its contents and save as `ROLE_OVERRIDES`.

## Build Sub-Agent Prompt

Read the agent prompt template: `reference/agent-prompt.md`

Read the design templates:
- `reference/high-level-design-template.md`
- `reference/component-design-template.md`
- `reference/design-template.md`

Combine all gathered context into a single prompt for the sub-agent. The prompt must include:

1. The contents of `reference/agent-prompt.md`
2. The design templates (include their contents inline so the sub-agent can reference them)
3. `ROLE_OVERRIDES` (if any), prefixed with "## Team Overrides\nFollow these additional instructions:\n"
4. The feature slug, workstream feature directory path, and context export path as concrete values (replace all placeholders)
5. `PM_CONTEXT` (if any), prefixed with "## Cross-Role Context (Product Manager)\nThe Product Manager recorded the following context during feature definition:\n"
6. `PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\nYou have been invoked before for this workstream. Here is context from your previous session:\n"
7. The user's arguments: `$ARGUMENTS`

## Dispatch Sub-Agent

Use the **Task tool** to launch a sub-agent:
- `subagent_type`: `"general-purpose"`
- `description`: `"System Architect: design <feature_slug>"`
- `prompt`: The combined prompt built above

Wait for the sub-agent to complete.

## Post Sub-Agent

1. Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

2. Report the sub-agent's results to the user.

3. Tell the user:

> **Next step:** Run `/sdd-stories <feature-name>` to generate user stories from this design.
