---
name: ssdd-stories
description: Generate user stories from a feature spec and design. Use after /ssdd-design to decompose a feature into stories with acceptance criteria. Stories are created in the work channel (epic).
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name>"
---

# Phase: Story Generation (Orchestrator)

You are the orchestrator for the Product Manager (Stories) phase. You will gather context, then dispatch a sub-agent to do the actual story generation work.

## Pre-Checks

Before proceeding, verify the required inputs exist:

1. Check that the feature exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" find-feature $ARGUMENTS
```
If this fails, STOP and tell the user: "Feature not found. Run `/ssdd-feature` first to create a feature specification."

Save the output as `<feature_slug>`.

2. Check that an epic with a high_level_design.md exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" find-epic $ARGUMENTS
```
If this fails, STOP and tell the user: "No epic found. Run `/ssdd-design <feature-name>` first to create the high-level design."

Save the output as `<epic_dir>`. Verify that `<epic_dir>/high_level_design.md` exists. If not, STOP and tell the user: "No epic found. Run `/ssdd-design <feature-name>` first to create the high-level design."

## Approval Check

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" check-approval design $ARGUMENTS
```

Parse the JSON output. If `approved` is `false`, display the list of unapproved artifacts and ask the user:

> **Warning:** The following artifacts from the previous step have not been approved:
> - _(list each path from the `unapproved` array)_
>
> Run `/ssdd-approve design <name>` to approve, or confirm you want to continue without approval.
> **Continue without approval?**

If the user says "no" or does not confirm, STOP. If the user says "yes" or explicitly opts in, proceed.

If `approved` is `true`, proceed silently.

## Context Import

1. Read prior agent context for the product_manager role:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" read-context product_manager --epic <epic_dir>
```
Save any output as `PRIOR_CONTEXT`.

2. Get the context export path:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" context-path product_manager --epic <epic_dir>
```
Save the output as `<context_export_path>`.

3. Check for cross-role context from the Product Manager (feature definition phase):
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" read-context product_manager --feature .ssdd/specs/<feature_slug>
```
Save any output as `PM_FEATURE_CONTEXT`.

4. Check for cross-role context from the System Architect:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" read-context system_architect --epic <epic_dir>
```
Save any output as `ARCHITECT_CONTEXT`.

## Team Overrides

Check if `.roles/product_manager.md` exists. If it does, read its contents and save as `ROLE_OVERRIDES`.

## Build Sub-Agent Prompt

Read the agent prompt template: `reference/agent-prompt.md`

Read the story template: `reference/story-template.md`

Combine all gathered context into a single prompt for the sub-agent. The prompt must include:

1. The contents of `reference/agent-prompt.md`
2. The story template contents (inline so the sub-agent can reference it)
3. `ROLE_OVERRIDES` (if any), prefixed with "## Team Overrides\nFollow these additional instructions:\n"
4. The feature slug, epic directory path, and context export path as concrete values (replace all placeholders)
5. `ARCHITECT_CONTEXT` (if any), prefixed with "## Cross-Role Context (System Architect)\nThe System Architect recorded the following context during design:\n"
6. `PM_FEATURE_CONTEXT` (if any), prefixed with "## Cross-Role Context (Feature Definition)\nThe Product Manager recorded the following context during feature definition:\n"
7. `PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\nYou have been invoked before for this epic. Here is context from your previous session:\n"
8. The user's arguments: `$ARGUMENTS`

## Dispatch Sub-Agent

Use the **Task tool** to launch a sub-agent:
- `subagent_type`: `"general-purpose"`
- `description`: `"Product Manager: generate stories"`
- `prompt`: The combined prompt built above

Wait for the sub-agent to complete.

## Post Sub-Agent

1. Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" regenerate-index
```

2. Report the sub-agent's results to the user.

3. Display a **Files to review** section listing every file that was created or modified. Use this format:

> **Files to review:**
>
> Stories:
> - `.ssdd/work/EPIC_NNN_slug/stories/STORY_NNN/story.md`
> - _(list all)_

List the actual file paths that were generated — do not use glob patterns.

4. Tell the user:

> **Next step:** Review the files above, then run `/ssdd-approve stories <epic-name>` to approve. Then run `/ssdd-tasks <feature-name>` to generate implementation tasks.
