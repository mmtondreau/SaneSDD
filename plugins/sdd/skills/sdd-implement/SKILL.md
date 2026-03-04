---
name: sdd-implement
description: Implement a single story through the Developer, Code Review, Task QA, Story QA, and Tech Lead remediation loop on a dedicated story branch.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<story-id-or-slug>"
---

# Implementation Loop (Orchestrator)

You are the orchestrator for the implementation loop. You will cycle through multiple roles by dispatching sub-agents for each phase. Each sub-agent operates in isolation with its own context. You manage the overall flow.

## Pre-Checks

Parse arguments: the argument is a story identifier (ID like `STORY_001`, slug like `STORY_001_user_login`, or substring like `user_login`).

Before proceeding, verify the required inputs exist:

1. Check that the story exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-story <argument>
```
If this fails, STOP and tell the user: "Story not found. Run `/sdd-stories <feature-name>` first to generate user stories."

Parse the JSON output to get `<story_path>`, `<story_id>`, `<feature_dir>`, `<feature_slug>`, `<epic_dir>`, and `<epic_slug>`.

2. Check that the epic exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-epic <feature_slug>
```
If this fails, STOP and tell the user: "No epic found. Run `/sdd-design <feature-name>` first to create the high-level design."

Save the output as `<epic_dir>`.

3. Check that the development plan exists and contains this story:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" plan-json <epic_slug>
```
If this fails, STOP and tell the user: "No development plan found. Run `/sdd-plan <feature-name>` first to create the execution plan."

Save the JSON output as `<plan_json>`. Parse it and extract only the story entry matching `<story_id>`. If the story is not in the plan, STOP and tell the user: "Story `<story_id>` is not in the development plan. Run `/sdd-plan <feature-name>` to regenerate."

Save the matching story's task list as `<story_tasks>`.

## Approval Check

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" check-approval plan <epic_slug>
```

Parse the JSON output. If `approved` is `false`, display the list of unapproved artifacts and ask the user:

> **Warning:** The following artifacts from the previous step have not been approved:
> - _(list each path from the `unapproved` array)_
>
> Run `/sdd-approve plan <name>` to approve, or confirm you want to continue without approval.
> **Continue without approval?**

If the user says "no" or does not confirm, STOP. If the user says "yes" or explicitly opts in, proceed.

If `approved` is `true`, proceed silently.

## Team Overrides

Before starting, check for and read these files if they exist. Save each as the corresponding variable:
- `.roles/developer.md` → `DEVELOPER_OVERRIDES`
- `.roles/code_reviewer.md` → `CODE_REVIEWER_OVERRIDES`
- `.roles/task_qa.md` → `TASK_QA_OVERRIDES`
- `.roles/story_qa.md` → `STORY_QA_OVERRIDES`
- `.roles/tech_lead.md` → `TECH_LEAD_OVERRIDES`

## Context Import (All Roles)

Read prior context for all five roles. For each role, run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" read-context <role> --epic <epic_dir>
```
Where `<role>` is: `developer`, `code_reviewer`, `task_qa`, `story_qa`, `tech_lead`.

Save each non-empty result as `<ROLE>_PRIOR_CONTEXT`.

Also get context export paths for all five roles:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" context-path <role> --epic <epic_dir>
```
Save each as `<role>_context_export_path`.

## Branch Setup

Before processing the story, create a dedicated git branch:

1. Derive the branch name from the story directory name. If the story directory is `STORY_001_user_login`, the branch name is `story/STORY_001_user_login`.

2. Check if the branch already exists:
```bash
git branch --list "story/<branch_name>"
```

3. If the branch exists, switch to it:
```bash
git checkout "story/<branch_name>"
```
This supports resuming a partially-completed story.

4. If the branch does NOT exist, create and switch to it:
```bash
git checkout -b "story/<branch_name>"
```

5. Verify you are on the correct branch:
```bash
git branch --show-current
```

## Execution Loop

### Step 1: Check Story Status
Read the story file at `<story_path>`. If status is already `DONE`, STOP and tell the user: "Story `<story_id>` is already DONE. Run `/sdd-merge <story_id>` to merge the story branch."

### Step 2: Mark Story IN_PROGRESS
Update the story file's frontmatter: set `status` to `IN_PROGRESS` and `updated` to today's date.

### Step 3: Process Each Task

For each task in `<story_tasks>` (in plan order), skip if status is already `DONE`:

#### Phase A: DEVELOPER Sub-Agent

Read `reference/agent-prompt-developer.md`.

Build a prompt that includes:
1. The agent-prompt-developer.md contents
2. `DEVELOPER_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `DEVELOPER_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The task spec path, story path, feature slug, epic_dir, and `developer_context_export_path` as concrete values
5. Instruction to read the specific task file and its parent story before starting work
6. If re-invoked after a code review rejection, include the `review_notes` from the task frontmatter, prefixed with "## Code Review Feedback\n"
7. If re-invoked after a Task QA failure, include the `qa_notes` from the task frontmatter, prefixed with "## QA Feedback\n"

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Developer: implement <task_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `DEVELOPER_PRIOR_CONTEXT` by reading the developer context file (it was just written by the sub-agent).

#### Phase A2: CODE REVIEWER Sub-Agent

Read `reference/agent-prompt-code-reviewer.md`.

Build a prompt that includes:
1. The agent-prompt-code-reviewer.md contents
2. `CODE_REVIEWER_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `CODE_REVIEWER_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The task spec path, story path, feature slug, epic_dir, and `code_reviewer_context_export_path` as concrete values
5. Instruction to read the specific task file and review all code changes for this task

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Code Review: review <task_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `CODE_REVIEWER_PRIOR_CONTEXT` by reading the code_reviewer context file.

#### Phase A3: Check Review Result

Re-read the task file. Check the `code_review` frontmatter field.

If `code_review` is `"APPROVED"`, proceed to Phase B (Task QA).

If `code_review` is `"CHANGES_REQUESTED"`, go back to Phase A (Developer). The `review_notes` from the task frontmatter will be included in the developer prompt. This counts toward the 3-attempt limit.

#### Phase B: TASK QA Sub-Agent

Read `reference/agent-prompt-task-qa.md`.

Build a prompt that includes:
1. The agent-prompt-task-qa.md contents
2. `TASK_QA_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `TASK_QA_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The task spec path, story path, feature slug, epic_dir, and `task_qa_context_export_path` as concrete values
5. Instruction to read the specific task file before starting validation

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Task QA: validate <task_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `TASK_QA_PRIOR_CONTEXT` by reading the task_qa context file.

#### Phase C: Check Result and Retry

Re-read the task file. If status is `DONE`, move to the next task.

If status is NOT `DONE`, go back to Phase A (Developer) to fix the issues. The `qa_notes` from the task frontmatter will be included in the developer prompt. The developer's changes will go through Code Review again before reaching Task QA.

You have up to **3 attempts total** per task (counting total Developer invocations regardless of whether the retry was triggered by code review rejection or QA failure). After 3 failed attempts, set the task status to `BLOCKED` and move to the next task.

### Step 4: STORY QA Sub-Agent

After all tasks for the story have been processed:

Read `reference/agent-prompt-story-qa.md`.

Build a prompt that includes:
1. The agent-prompt-story-qa.md contents
2. `STORY_QA_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `STORY_QA_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The story path, all task paths for this story, feature slug, epic_dir, and `story_qa_context_export_path` as concrete values

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Story QA: validate <story_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `STORY_QA_PRIOR_CONTEXT` by reading the story_qa context file.

### Step 4b: Story Promotion

Re-read the story file. If the story status is `DONE` (Story QA passed), promote the work story to the spec channel:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" promote-story <story_path> --epic <epic_dir>
```

If the story is not `DONE`, skip this step and proceed to Step 5 (Remediation).

### Step 5: REMEDIATION (if story not DONE)

Re-read the story file. If status is `DONE`, proceed to After Story Processing.

If status is NOT `DONE`:

Read `reference/agent-prompt-tech-lead.md`.

Build a prompt that includes:
1. The agent-prompt-tech-lead.md contents
2. `TECH_LEAD_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `TECH_LEAD_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The story path, `<epic_dir>/stories/<story_id>/` as the story directory, feature slug, epic_dir, and `tech_lead_context_export_path` as concrete values
5. The list of incomplete ACs from the story file

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Tech Lead: remediate <story_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `TECH_LEAD_PRIOR_CONTEXT` by reading the tech_lead context file.

After remediation, the new tasks need to be processed. Re-read the story's task directory for new TASK files with status TODO, and loop back to Step 3 for those tasks.

## After Story Processing

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

Report a summary of results:
- Story ID and title
- Branch name: `story/<branch_name>`
- How many tasks were processed
- How many tasks are DONE vs incomplete
- Any tasks that ended up BLOCKED
- Any ACs that remain incomplete

Display a **Files to review** section listing every file that was created or modified, grouped by type. Use this format:

> **Files to review:**
>
> Updated stories and tasks:
> - `work/EPIC_NNN_slug/stories/STORY_NNN/story.md`
> - `work/EPIC_NNN_slug/stories/STORY_NNN/TASK_NNN_slug.md`
> - _(list all updated)_
>
> Promoted spec stories (if any):
> - `specs/THEME_NNN_slug/features/FEAT_NNN_slug/stories/STORY_NNN_slug.md`
> - _(list all promoted)_

List the actual file paths — do not use glob patterns.

If the story is DONE, tell the user:

> **Story complete!** Run `/sdd-merge <story_id>` to merge the story branch to main.

If the story is NOT complete, tell the user:

> **Story incomplete.** Review the blocked tasks above, then re-run `/sdd-implement <story_id>` to continue.
