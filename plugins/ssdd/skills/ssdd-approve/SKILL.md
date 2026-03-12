---
name: ssdd-approve
description: Approve artifacts after review. Run after reviewing the output of any SaneSDD step. Approves individual files by path.
disable-model-invocation: true
user-invocable: true
argument-hint: "<file-path> [<file-path> ...]"
---

# Approve SaneSDD Artifacts

This skill records user approval of individual artifact files. It is a deterministic operation — no sub-agent is dispatched.

## Usage

```
/ssdd-approve <file-path> [<file-path> ...]
```

Where `<file-path>` is the path to one or more artifact files to approve. Paths can be absolute or relative to the project root.

**Examples:**
```
/ssdd-approve .ssdd/specs/THEME_001_checkout/features/FEAT_001_checkout/feature.md
/ssdd-approve .ssdd/work/EPIC_001_checkout/high_level_design.md
/ssdd-approve .ssdd/work/EPIC_001_checkout/stories/STORY_001/story.md .ssdd/work/EPIC_001_checkout/stories/STORY_002/story.md
/ssdd-approve .ssdd/work/EPIC_001_checkout/stories/STORY_001/TASK_001_auth.md
/ssdd-approve .ssdd/work/EPIC_001_checkout/development_plan.yaml
```

## Step 1: Parse Arguments

Parse `$ARGUMENTS` to extract one or more file paths.

If no arguments are provided, tell the user the expected usage:

> **Usage:** `/ssdd-approve <file-path> [<file-path> ...]`
>
> Approve individual artifact files by path. The `approved` field in the file's frontmatter will be set to today's date.
>
> **Approvable files:**
> | File | Typical path |
> |------|-------------|
> | Feature spec | `.ssdd/specs/THEME_NNN_*/features/FEAT_NNN_*/feature.md` |
> | High-level design | `.ssdd/work/EPIC_NNN_*/high_level_design.md` |
> | Work story | `.ssdd/work/EPIC_NNN_*/stories/STORY_NNN/story.md` |
> | Task | `.ssdd/work/EPIC_NNN_*/stories/STORY_NNN/TASK_NNN_*.md` |
> | Development plan | `.ssdd/work/EPIC_NNN_*/development_plan.yaml` |

Then STOP.

## Step 2: Run Approval

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" approve-file <file-path> [<file-path> ...]
```

If the command fails, report the error to the user and STOP.

## Step 3: Report Results

Parse the JSON output. Display the results:

> **Approved:**
> - `<path1>` (approved: YYYY-MM-DD)
> - `<path2>` (approved: YYYY-MM-DD)
> - _(list all approved files)_

If there were any errors (partial approval), also display:

> **Errors:**
> - _(list each error)_

## Step 4: Suggest Next Step

Based on the file type(s) that were approved, tell the user what to run next:

| Approved file type | Next Step |
|-------------------|-----------|
| `feature.md` | `/ssdd-design <feature-name>` |
| `high_level_design.md` | `/ssdd-stories <feature-name>` |
| `story.md` | `/ssdd-tasks <feature-name>` |
| `TASK_*.md` | `/ssdd-plan <feature-name>` |
| `development_plan.yaml` | `/ssdd-implement <epic-name>` |

## User Input
$ARGUMENTS
