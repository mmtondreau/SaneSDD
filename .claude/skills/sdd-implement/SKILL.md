---
name: sdd-implement
description: Execute the full implementation loop for a feature. Cycles through Developer, Task QA, Story QA, and Tech Lead remediation roles for each story in plan order.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name> [story-filter]"
---

# Implementation Loop

## Overview
You will implement a feature by cycling through multiple roles for each story and task. This is a structured, multi-phase process. Follow it precisely.

For detailed role profiles, see the reference files in this skill's directory.

## Setup

Parse arguments: the first word is the feature name, the optional second word is a story filter.

1. Find the feature:
```bash
poetry run sdd-util find-feature <feature-name>
```

2. Find the workstream:
```bash
poetry run sdd-util find-workstream <feature-name>
```

3. Load the execution plan:
```bash
poetry run sdd-util plan-json <feature-name>
```

The plan-json command outputs a JSON structure listing stories and tasks in execution order. Parse it and iterate through each story.

## Team Overrides
Before starting, check for and read these files if they exist:
- `.roles/developer.md`
- `.roles/task_qa.md`
- `.roles/story_qa.md`
- `.roles/tech_lead.md`

Follow their instructions during the corresponding phases below.

## Execution Loop

For each story in plan order:

### Step 1: Check Story Status
Read the story file. If status is already `DONE`, skip it and move to the next story.

### Step 2: Mark Story IN_PROGRESS
Update the story file's frontmatter: set `status` to `IN_PROGRESS` and `updated` to today's date.

### Step 3: Process Each Task

For each task in the story (in plan order), skip if status is already `DONE`:

#### Phase A: DEVELOPER

**You are now the Developer.** Read the Developer role profile in `reference/role-profiles.md` and the implementation phase instructions in `reference/implementation-loop.md`.

Key responsibilities:
- Read the task spec and parent story
- Read relevant design documents (`design/design.md`, `design/COMP_*.md`)
- Read existing code in areas you will modify
- Implement the solution: write production code, write unit tests (80% line coverage minimum)
- Use dependency injection for all external collaborators
- Run linters and fix violations
- Run tests — all must pass
- Update the task frontmatter: set `status` to `DONE` and `updated` to today's date
- Run `poetry run sdd-util regenerate-index`

#### Phase B: TASK QA

**You are now Task QA. You MUST NOT modify any source code or test files during this phase.** Read the Task QA role profile in `reference/role-profiles.md` and the task QA instructions in `reference/implementation-loop.md`.

Execute ALL validation steps in order:
1. **Done Criteria Check** — Read the task spec's "Done Criteria". For each criterion, verify it is satisfied.
2. **Test Existence Check** — Verify test files exist for each production module created or modified.
3. **Lint Check** — Run the project's lint command. PASS if exit code 0.
4. **Test Execution Check** — Run the project's test command. PASS if all tests pass.
5. **Coverage Check** — Verify line coverage >= 80% for modules the task touched.
6. **Design Documentation Check** — If the task changed any interface or architecture, verify design docs are updated.
7. **INDEX.md Check** — Verify INDEX.md has entries for every file created or modified.

If ALL checks pass: update the task frontmatter `status` to `DONE`.
If ANY check fails: leave status as `IN_PROGRESS` and add a `qa_notes` field to frontmatter describing what failed.

#### Phase C: Check Result and Retry

Re-read the task file. If status is `DONE`, move to the next task.

If status is NOT `DONE`, go back to Phase A (Developer) and fix the issues noted in `qa_notes`. You have up to **3 attempts total** per task.

After 3 failed attempts, set the task status to `BLOCKED` and move to the next task.

### Step 4: STORY QA

**You are now Story QA. You MUST NOT modify any source code, test files, or spec files during this phase.** Read the Story QA role profile in `reference/role-profiles.md` and the story QA instructions in `reference/implementation-loop.md`.

Execute ALL validation steps:
1. **Task Completion Check** — For each task belonging to this story, verify its status is `DONE`.
2. **AC-to-Task Mapping Check** — For each AC, find all tasks whose `ac_mapping` includes this AC. Flag any ACs with no mapped tasks.
3. **AC Satisfaction Check** — For each AC, examine the implementation and tests. Run relevant tests. Verdict each AC as PASS or FAIL with evidence.
4. **Dependency Check** — For each story ID in `depends_on`, verify that story's status is `DONE`.
5. **Regression Tests** — Run the full test suite to verify no regressions.

If ALL checks pass: update each AC status to `DONE` in the story frontmatter, then set story status to `DONE`.
If ANY check fails: leave failed ACs as `TODO`. List all blocking issues.

### Step 5: REMEDIATION (if story not DONE)

**You are now the Tech Lead.** Read the Tech Lead role profile in `reference/role-profiles.md`.

For each incomplete AC:
1. Determine what additional work is needed.
2. Create new TASK files for the remediation work.
3. Map each new task to the ACs it will satisfy.
4. Set `depends_on` for new tasks as appropriate.
5. Set new task status to `TODO`.

Determine the next task number:
```bash
poetry run sdd-util next-task-number <ws_story_dir>
```

Write new task files to: `<ws_story_dir>/TASK_NNN_<slug>.md`

## After All Stories

Run:
```bash
poetry run sdd-util regenerate-index
```

Report a summary of results:
- How many stories were processed
- How many stories are DONE vs incomplete
- Any tasks that ended up BLOCKED
- Any ACs that remain incomplete
