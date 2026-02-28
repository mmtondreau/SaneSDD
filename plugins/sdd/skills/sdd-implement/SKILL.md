---
name: sdd-implement
description: Execute the full implementation loop for a feature. Cycles through Developer, Task QA, Story QA, and Tech Lead remediation roles for each story in plan order.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name> [story-filter]"
---

# Implementation Loop (Orchestrator)

You are the orchestrator for the implementation loop. You will cycle through multiple roles by dispatching sub-agents for each phase. Each sub-agent operates in isolation with its own context. You manage the overall flow.

## Pre-Checks

Parse arguments: the first word is the feature name, the optional second word is a story filter.

Before proceeding, verify the required inputs exist:

1. Check that the feature exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-feature <feature-name>
```
If this fails, STOP and tell the user: "Feature not found. Run `/sdd-feature` first to create a feature specification."

Save the output as `<feature_slug>`.

2. Check that the workstream exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-workstream <feature-name>
```
If this fails, STOP and tell the user: "No workstream found. Run `/sdd-design <feature-name>` first to create the high-level design."

Save the output as `<ws_feature_dir>`.

3. Check that the development plan exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" plan-json <feature-name>
```
If this fails, STOP and tell the user: "No development plan found. Run `/sdd-plan <feature-name>` first to create the execution plan."

Save the JSON output as `<plan_json>`.

## Team Overrides

Before starting, check for and read these files if they exist. Save each as the corresponding variable:
- `.roles/developer.md` → `DEVELOPER_OVERRIDES`
- `.roles/task_qa.md` → `TASK_QA_OVERRIDES`
- `.roles/story_qa.md` → `STORY_QA_OVERRIDES`
- `.roles/tech_lead.md` → `TECH_LEAD_OVERRIDES`

## Context Import (All Roles)

Read prior context for all four roles. For each role, run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" read-context <role> --workstream <ws_feature_dir>
```
Where `<role>` is: `developer`, `task_qa`, `story_qa`, `tech_lead`.

Save each non-empty result as `<ROLE>_PRIOR_CONTEXT`.

Also get context export paths for all four roles:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" context-path <role> --workstream <ws_feature_dir>
```
Save each as `<role>_context_export_path`.

## Execution Loop

Parse `<plan_json>` to get the ordered list of stories and tasks. For each story in plan order:

### Step 1: Check Story Status
Read the story file. If status is already `DONE`, skip it and move to the next story.

If a story filter was provided, skip stories that don't match.

### Step 2: Mark Story IN_PROGRESS
Update the story file's frontmatter: set `status` to `IN_PROGRESS` and `updated` to today's date.

### Step 3: Process Each Task

For each task in the story (in plan order), skip if status is already `DONE`:

#### Phase A: DEVELOPER Sub-Agent

Read `reference/agent-prompt-developer.md`.

Build a prompt that includes:
1. The agent-prompt-developer.md contents
2. `DEVELOPER_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `DEVELOPER_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The task spec path, story path, feature slug, ws_feature_dir, and `developer_context_export_path` as concrete values
5. Instruction to read the specific task file and its parent story before starting work

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Developer: implement <task_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `DEVELOPER_PRIOR_CONTEXT` by reading the developer context file (it was just written by the sub-agent).

#### Phase B: TASK QA Sub-Agent

Read `reference/agent-prompt-task-qa.md`.

Build a prompt that includes:
1. The agent-prompt-task-qa.md contents
2. `TASK_QA_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `TASK_QA_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The task spec path, story path, feature slug, ws_feature_dir, and `task_qa_context_export_path` as concrete values
5. Instruction to read the specific task file before starting validation

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Task QA: validate <task_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `TASK_QA_PRIOR_CONTEXT` by reading the task_qa context file.

#### Phase C: Check Result and Retry

Re-read the task file. If status is `DONE`, move to the next task.

If status is NOT `DONE`, go back to Phase A (Developer) and fix the issues. Include the `qa_notes` from the task frontmatter in the developer sub-agent prompt so it knows what to fix.

You have up to **3 attempts total** per task. After 3 failed attempts, set the task status to `BLOCKED` and move to the next task.

### Step 4: STORY QA Sub-Agent

After all tasks for a story have been processed:

Read `reference/agent-prompt-story-qa.md`.

Build a prompt that includes:
1. The agent-prompt-story-qa.md contents
2. `STORY_QA_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `STORY_QA_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The story path, all task paths for this story, feature slug, ws_feature_dir, and `story_qa_context_export_path` as concrete values

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Story QA: validate <story_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `STORY_QA_PRIOR_CONTEXT` by reading the story_qa context file.

### Step 5: REMEDIATION (if story not DONE)

Re-read the story file. If status is `DONE`, move to the next story.

If status is NOT `DONE`:

Read `reference/agent-prompt-tech-lead.md`.

Build a prompt that includes:
1. The agent-prompt-tech-lead.md contents
2. `TECH_LEAD_OVERRIDES` (if any), prefixed with "## Team Overrides\n"
3. `TECH_LEAD_PRIOR_CONTEXT` (if any), prefixed with "## Prior Context\n"
4. The story path, ws_story_dir, feature slug, ws_feature_dir, and `tech_lead_context_export_path` as concrete values
5. The list of incomplete ACs from the story file

Dispatch via **Task tool**:
- `subagent_type`: `"general-purpose"`
- `description`: `"Tech Lead: remediate <story_id>"`
- `prompt`: The combined prompt

Wait for completion. Update `TECH_LEAD_PRIOR_CONTEXT` by reading the tech_lead context file.

After remediation, the new tasks need to be processed. Re-read the story's task directory for new TASK files with status TODO, and loop back to Step 3 for those tasks.

## After All Stories

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

Report a summary of results:
- How many stories were processed
- How many stories are DONE vs incomplete
- Any tasks that ended up BLOCKED
- Any ACs that remain incomplete

If any stories remain incomplete, tell the user:

> **Next step:** Review the blocked tasks above, then re-run `/sdd-implement <feature-name>` to continue.

If all stories are DONE, tell the user:

> **All stories complete!** The feature implementation is finished.
