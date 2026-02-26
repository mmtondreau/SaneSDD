---
name: sdd-tasks
description: Generate implementation tasks from stories and design documents. Use after /sdd-stories to break stories into developer tasks.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name>"
---

# Phase: Task Generation

## Your Role: Tech Lead

You are the Tech Lead. You own the development plan. You bridge the gap between design and implementation by decomposing stories into tasks, sequencing work, and watching for spec drift and risk.

### Hard Constraints
- You MUST NOT modify feature specs or story acceptance criteria (PM owns those).
- You MUST NOT write implementation code or tests.
- You MUST NOT schedule a task before all its dependencies.
- Every AC across all stories MUST be covered by at least one task's ac_mapping.
- When you detect spec drift, flag it with affected artifact IDs.

### Artifacts You Own
- work/WS_*/FEAT_*/stories/STORY_*/TASK_*.md
- work/WS_*/FEAT_*/development_plan.yaml

## Team Overrides
If the file `.roles/tech_lead.md` exists in the project root, read it and follow those additional instructions.

## Pre-Checks

Before proceeding, verify the required inputs exist:

1. Check that the feature exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-feature $ARGUMENTS
```
If this fails, STOP and tell the user: "Feature not found. Run `/sdd-feature` first to create a feature specification."

2. Check that the workstream exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-workstream $ARGUMENTS
```
If this fails, STOP and tell the user: "No workstream found. Run `/sdd-design <feature-name>` first to create the high-level design."

3. Check that stories exist by globbing for `specs/<feature_slug>/stories/STORY_*.md`.
If no stories are found, STOP and tell the user: "No stories found. Run `/sdd-stories <feature-name>` first to generate user stories."

## Setup

The feature and workstream paths were found during pre-checks. Use those paths for the rest of this skill.

## Objective
Generate implementation tasks from stories and design documents. Only target stories that are NOT marked DONE.

## Context Gathering
Read the following files:
1. The feature spec: `specs/<feature_slug>/feature.md`
2. All stories: glob for `specs/<feature_slug>/stories/STORY_*.md`
3. Global design docs: `design/design.md` and `design/COMP_*.md`
4. The workstream design: `<ws_feature_dir>/high_level_design.md`

## Process
1. Read all stories for the feature (skip DONE stories).
2. Read the high-level design and global design docs.
3. For each non-DONE story, identify technical work to satisfy its ACs.
4. Decompose into discrete tasks (one PR per task).
5. Map each task to the ACs it satisfies.
6. Declare dependencies between tasks.
7. Verify complete AC coverage.

## Task File Schema

Frontmatter:
```yaml
---
id: "TASK_NNN"
title: "<task title>"
status: "TODO"
story: "STORY_NNN"
depends_on: []
ac_mapping: ["AC_NNN"]
created: "<today's date YYYY-MM-DD>"
updated: "<today's date YYYY-MM-DD>"
---
```

Body:
```markdown
## Description
[What needs to be built or changed]

## Done Criteria
- [Specific, verifiable condition 1]
- [Specific, verifiable condition 2]

## Technical Approach
[How to implement. Reference design docs.]

## Test Plan
[What tests need to be written]

## Files to Create or Modify
- src/path/to/file.py (create/modify)
- tests/test_file.py (create)
```

## Template
Read the template at `reference/task-template.md` and use it as the structural guide for each task file.

## Rules
- Every AC across all non-DONE stories MUST appear in at least one task's ac_mapping.
- A single task should be completable in one focused session.
- Task dependencies MUST respect story dependencies.
- Each task maps to a single Pull Request.

Create story directories and determine task numbers:
```bash
# For each story that needs tasks:
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" next-task-number <ws_feature_dir>/stories/STORY_NNN
```

## AC Coverage Verification
After generating all tasks, verify coverage:
| AC ID | Mapped Tasks |
|-------|-------------|
Flag any gaps.

## Output Location
Write files to: `<ws_feature_dir>/stories/STORY_NNN/TASK_NNN_<slug>.md`
Create the story subdirectory if it doesn't exist.

## After Completion
Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

After regenerating the index, tell the user:

> **Next step:** Run `/sdd-plan <feature-name>` to create the execution plan.
