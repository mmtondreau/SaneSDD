---
name: ssdd-plan
description: Generate a sequenced development_plan.yaml that orders stories and tasks for implementation. Use after /ssdd-tasks.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name>"
---

# Phase: Development Plan (Orchestrator)

You are the orchestrator for the Tech Lead (Plan) phase. You will gather context, then dispatch a sub-agent to do the actual planning work.

## Pre-Checks

Before proceeding, verify the required inputs exist:

1. Check that the feature exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" find-feature $ARGUMENTS
```
If this fails, STOP and tell the user: "Feature not found. Run `/ssdd-feature` first to create a feature specification."

Save the output as `<feature_slug>`.

2. Check that the epic exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" find-epic $ARGUMENTS
```
If this fails, STOP and tell the user: "No epic found. Run `/ssdd-design <feature-name>` first to create the high-level design."

Save the output as `<epic_dir>`.

3. Check that tasks exist by globbing for `<epic_dir>/stories/*/TASK_*.md`.
If no tasks are found, STOP and tell the user: "No tasks found. Run `/ssdd-tasks <feature-name>` first to generate implementation tasks."

## Approval Check

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" check-approval tasks $ARGUMENTS
```

Parse the JSON output. If `approved` is `false`, display the list of unapproved artifacts and ask the user:

> **Warning:** The following artifacts from the previous step have not been approved:
> - _(list each path from the `unapproved` array)_
>
> Approve each file by running `/ssdd-approve <file-path>` for each unapproved file listed above, or confirm you want to continue without approval.
> **Continue without approval?**

If the user says "no" or does not confirm, STOP. If the user says "yes" or explicitly opts in, proceed.

If `approved` is `true`, proceed silently.

## Context Import

1. Read prior agent context for the tech_lead role:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" read-context tech_lead --epic <epic_dir>
```
Save any output as `PRIOR_CONTEXT`. This may include context from the `/ssdd-tasks` phase since both use the tech_lead role.

2. Get the context export path:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" context-path tech_lead --epic <epic_dir>
```
Save the output as `<context_export_path>`.

## Team Overrides

Check if `.roles/tech_lead.md` exists. If it does, read its contents and save as `ROLE_OVERRIDES`.

## Build Sub-Agent Prompt

Read the agent prompt template: `reference/agent-prompt.md`

Read the plan template: `reference/development-plan-template.yaml`

Combine all gathered context into a single prompt for the sub-agent. The prompt must include:

1. The contents of `reference/agent-prompt.md`
2. The plan template contents (inline so the sub-agent can reference it)
3. `ROLE_OVERRIDES` (if any), prefixed with "## Team Overrides\nFollow these additional instructions:\n"
4. The feature slug, epic directory path, and context export path as concrete values (replace all placeholders)
5. `PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\nYou have been invoked before for this epic. Here is context from your previous session:\n"
6. The user's arguments: `$ARGUMENTS`

## Dispatch Sub-Agent

Use the **Task tool** to launch a sub-agent:
- `subagent_type`: `"general-purpose"`
- `description`: `"Tech Lead: create development plan"`
- `prompt`: The combined prompt built above

Wait for the sub-agent to complete.

## Post Sub-Agent

1. Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" regenerate-index
```

2. Report the sub-agent's results to the user.

3. Generate and display the **Files to review** section:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" files-to-review plan <feature-name>
```
Display the output to the user exactly as returned.

## User Action

After displaying the files-to-review output, wait for the user's response:

- If the user responds with **A** (approve): Run `/ssdd-approve` on all output files, then display the approval results.
- If the user responds with **C** (continue): Run `/ssdd-approve` on all output files first, then run `/ssdd-implement` for the first story in plan order (the continue command shown in the output).
- If the user responds with anything else, treat it as normal conversation.
