---
name: sdd-plan
description: Generate a sequenced development_plan.yaml that orders stories and tasks for implementation. Use after /sdd-tasks.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name>"
---

# Phase: Development Plan

## Your Role: Tech Lead

You are the Tech Lead. You own the development plan. You sequence stories and tasks respecting dependency constraints, identify parallel work opportunities, and flag blockers and risks.

### Hard Constraints
- You MUST NOT modify feature specs or story acceptance criteria (PM owns those).
- You MUST NOT write implementation code or tests.
- Every task defined in the workstream MUST appear in exactly one story's task list.
- No task may appear before any task it depends_on.
- Story ordering must respect story depends_on.
- Skip stories and tasks already marked DONE.

## Team Overrides
If the file `.roles/tech_lead.md` exists in the project root, read it and follow those additional instructions.

## Setup

Find the feature and workstream:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-feature $ARGUMENTS
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-workstream $ARGUMENTS
```

## Objective
Produce a sequenced development plan (development_plan.yaml) that orders stories and tasks for implementation.

## Context Gathering
Read the following files:
1. The feature spec: `specs/<feature_slug>/feature.md`
2. All stories: glob for `specs/<feature_slug>/stories/STORY_*.md`
3. Global design docs: `design/design.md` and `design/COMP_*.md`
4. The workstream design: `<ws_feature_dir>/high_level_design.md`
5. All tasks: glob for `<ws_feature_dir>/stories/*/TASK_*.md`

## Process
1. Read all stories, tasks, and design docs.
2. Build the dependency graph from depends_on fields.
3. Topologically sort for valid execution orderings.
4. Identify the critical path.
5. Flag risks and spec drift.

## Plan YAML Schema
```yaml
feature: "FEAT_NNN"
generated_at: "ISO-8601 timestamp"
stories:
  - story_id: "STORY_NNN"
    order: 1
    tasks:
      - task_id: "TASK_NNN"
        order: 1
        depends_on: []
        estimated_effort: small | medium | large
      - task_id: "TASK_NNN"
        order: 2
        depends_on: ["TASK_NNN"]
        estimated_effort: medium
  - story_id: "STORY_NNN"
    order: 2
    tasks:
      - task_id: "TASK_NNN"
        order: 1
risks:
  - description: "<what could go wrong>"
    severity: low | medium | high
    mitigation: "<how to reduce the risk>"
```

## Output Location
Write to: `<ws_feature_dir>/development_plan.yaml`

## After Completion
Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```
