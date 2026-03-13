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
/ssdd-approve <path> [<path> ...]
```

Where `<path>` is a file or directory. When a directory is given, all approvable files (`.md`, `.yaml`) under it are approved recursively.

Paths can be:
- Absolute
- Relative to the project root (e.g. `.ssdd/work/...`)
- Relative to `.ssdd/` (e.g. `work/...`, `specs/...`)

**Examples:**
```
/ssdd-approve specs/THEME_001_checkout/features/FEAT_001_checkout/feature.md
/ssdd-approve work/EPIC_001_checkout/high_level_design.md
/ssdd-approve work/EPIC_001_checkout/stories/STORY_001/story.md work/EPIC_001_checkout/stories/STORY_002/story.md
/ssdd-approve work/EPIC_001_checkout/stories/STORY_001/TASK_001_auth.md
/ssdd-approve work/EPIC_001_checkout/development_plan.yaml
/ssdd-approve work/EPIC_001_checkout/stories/STORY_001          # approves story.md + all tasks
/ssdd-approve work/EPIC_001_checkout/stories                    # approves all stories and tasks
/ssdd-approve work/EPIC_001_checkout                            # approves everything in the epic
```

## Step 1: Parse Arguments

Parse `$ARGUMENTS` to extract one or more file paths.

If no arguments are provided, tell the user the expected usage:

> **Usage:** `/ssdd-approve <path> [<path> ...]`
>
> Approve artifact files or directories by path. The `approved` field in each file's frontmatter will be set to today's date. Directories are approved recursively. Paths can be relative to `.ssdd/`.
>
> **Approvable files:**
> | File | Typical path |
> |------|-------------|
> | Feature spec | `specs/THEME_NNN_*/features/FEAT_NNN_*/feature.md` |
> | High-level design | `work/EPIC_NNN_*/high_level_design.md` |
> | Work story | `work/EPIC_NNN_*/stories/STORY_NNN/story.md` |
> | Task | `work/EPIC_NNN_*/stories/STORY_NNN/TASK_NNN_*.md` |
> | Development plan | `work/EPIC_NNN_*/development_plan.yaml` |
> | Directory | `work/EPIC_NNN_*/stories/STORY_NNN` (approves all files recursively) |

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

Based on the file type(s) that were approved, determine the next command:

| Approved file type | Next Step |
|-------------------|-----------|
| `feature.md` | `/ssdd-design <feature-name>` |
| `high_level_design.md` | `/ssdd-stories <feature-name>` |
| `story.md` | `/ssdd-tasks <feature-name>` |
| `TASK_*.md` | `/ssdd-plan <feature-name>` |
| `development_plan.yaml` | `/ssdd-implement <epic-name>` |

Display:

> ---
> **`[C]`** Continue — `<next-step-command>`

## User Action

After displaying the next step prompt, wait for the user's response:

- If the user responds with **C** (continue): Run the next step command shown above.
- If the user responds with anything else, treat it as normal conversation.

## User Input
$ARGUMENTS
