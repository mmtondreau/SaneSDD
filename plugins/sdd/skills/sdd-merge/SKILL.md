---
name: sdd-merge
description: Merge a completed story branch to the base branch after verifying all tasks are DONE, code review passed, and Story QA passed.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<story-id-or-slug>"
---

# Story Merge (Orchestrator)

You are the orchestrator for merging a completed story branch to the base branch. This is a deterministic process — you perform all checks and git operations directly without dispatching sub-agents.

## Pre-Checks

### 1. Find the Story

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-story $ARGUMENTS
```
If this fails, STOP and tell the user: "Story not found. Check the story ID and try again."

Parse the JSON output to get `<story_path>`, `<story_id>`, `<feature_dir>`, and `<feature_slug>`.

### 2. Verify Story is DONE

Read the story file at `<story_path>`. Check the frontmatter `status` field.

If status is NOT `DONE`, STOP and tell the user:

> Story `<story_id>` is not complete (status: `<status>`). Run `/sdd-implement <story_id>` to complete implementation first.

### 3. Find the Workstream

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-workstream <feature_slug>
```

Save the output as `<ws_feature_dir>`.

### 4. Verify All Tasks are DONE

Determine the workstream story directory: `<ws_feature_dir>/stories/<story_id>/`

Read all `TASK_*.md` files in that directory. For each task, check that frontmatter `status` is `DONE`.

If any task is NOT `DONE`, STOP and list the incomplete tasks:

> The following tasks are not complete:
> - `<task_id>`: status `<status>`
>
> Run `/sdd-implement <story_id>` to complete remaining tasks.

### 5. Verify Code Review Passed

For each task file, check that the `code_review` frontmatter field is `"APPROVED"`.

If any task does not have `code_review: "APPROVED"`, STOP and report:

> The following tasks have not passed code review:
> - `<task_id>`: code_review `<value or "missing">`
>
> Run `/sdd-implement <story_id>` to complete code review.

### 6. Verify Story Branch Exists

Derive the branch name from the story file name. If the story file is `STORY_001_user_login.md`, the branch name is `story/STORY_001_user_login`.

```bash
git branch --list "story/<branch_name>"
```

If the branch does not exist, STOP and tell the user:

> Story branch `story/<branch_name>` not found. The story may have been implemented without branching, or the branch was already merged/deleted.

## Merge

### 1. Switch to Base Branch

Check the current branch:
```bash
git branch --show-current
```

If not on `main`, switch to it:
```bash
git checkout main
```

### 2. Perform the Merge

Read the story title from the story frontmatter.

```bash
git merge --no-ff "story/<branch_name>" -m "Merge story/<branch_name>: <story_title>"
```

The `--no-ff` flag ensures a merge commit is created for traceability.

### 3. Handle Merge Result

**If merge succeeds:**

Delete the story branch:
```bash
git branch -d "story/<branch_name>"
```

Regenerate the index:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

**If merge fails (conflict):**

Report the conflicting files. Do NOT attempt automatic conflict resolution.

Abort the merge:
```bash
git merge --abort
```

Tell the user:

> Merge conflicts detected in the following files:
> - `<file1>`
> - `<file2>`
>
> Please resolve conflicts manually on the `story/<branch_name>` branch, then re-run `/sdd-merge <story_id>`.

STOP here — do not proceed to Post-Merge.

## Post-Merge

Report a summary:
- Story merged: `<story_id>` — `<story_title>`
- Branch merged: `story/<branch_name>` → `main`
- Tasks completed: `<count>`
- All acceptance criteria satisfied

Check if there are more stories for the feature that are not DONE. Read all story files in `<feature_dir>/stories/`. If any stories remain with status not `DONE`, tell the user:

> **Next step:** Run `/sdd-implement <next_story_id>` to implement the next story.

If ALL stories for the feature are `DONE`, update the feature frontmatter status to `DONE` and tell the user:

> **Feature complete!** All stories for `<feature_slug>` have been implemented and merged.
