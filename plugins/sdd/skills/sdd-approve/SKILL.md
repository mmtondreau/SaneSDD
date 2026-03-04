---
name: sdd-approve
description: Approve artifacts after review. Run after reviewing the output of any SDD step (feature, design, stories, tasks, plan).
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<step> <name>"
---

# Approve SDD Artifacts

This skill records user approval of artifacts produced by a workflow step. It is a deterministic operation — no sub-agent is dispatched.

## Usage

```
/sdd-approve <step> <name>
```

Where `<step>` is one of: `feature`, `design`, `stories`, `tasks`, `plan`.
And `<name>` is the feature name (for `feature`) or epic name (for all other steps).

## Step 1: Parse Arguments

Parse `$ARGUMENTS` to extract `<step>` and `<name>`.

If no arguments are provided, tell the user the expected usage:

> **Usage:** `/sdd-approve <step> <name>`
>
> | Step | What it approves | Name argument |
> |------|-----------------|---------------|
> | `feature` | `feature.md` | Feature name or ID |
> | `design` | `high_level_design.md` | Epic name or ID |
> | `stories` | All `story.md` in epic | Epic name or ID |
> | `tasks` | All `TASK_*.md` in epic | Epic name or ID |
> | `plan` | `development_plan.yaml` | Epic name or ID |

Then STOP.

If arguments are provided but invalid (wrong step name, missing name), explain the error and show the usage table above, then STOP.

## Step 2: Run Approval

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" approve <step> <name>
```

If the command fails, report the error to the user and STOP.

## Step 3: Report Results

Parse the JSON output. Display the results:

> **Approved:**
> - `<path1>`
> - `<path2>`
> - _(list all approved files)_

## Step 4: Suggest Next Step

Based on the step that was approved, tell the user what to run next:

| Approved Step | Next Step |
|--------------|-----------|
| `feature` | `/sdd-design <feature-name>` |
| `design` | `/sdd-stories <epic-name>` |
| `stories` | `/sdd-tasks <epic-name>` |
| `tasks` | `/sdd-plan <epic-name>` |
| `plan` | `/sdd-implement <epic-name>` |

## User Input
$ARGUMENTS
