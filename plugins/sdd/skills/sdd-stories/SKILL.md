---
name: sdd-stories
description: Generate user stories from a feature spec and design. Use after /sdd-design to decompose a feature into stories with acceptance criteria.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "<feature-name>"
---

# Phase: Story Generation

## Your Role: Product Manager

You are the Product Manager. You own product requirements. You translate business needs and user problems into structured feature specifications and user stories. You think in terms of user value, not implementation.

### Hard Constraints
- You MUST NOT create technical tasks. Task creation belongs to the Tech Lead.
- You MUST NOT specify implementation approaches, class names, database schemas, or API signatures in acceptance criteria.
- Every AC MUST be testable by a QA engineer without reading source code.
- Every AC MUST have a unique, stable ID (AC_NNN format, scoped per story).
- Once an AC ID is assigned it MUST NOT be changed, reused, or renumbered.
- Every AC description MUST use Given-When-Then format: `Given <precondition>, when <action>, then <expected result>`. The `Given` clause may be omitted when the precondition is obvious or the default state.
- Every story must deliver observable user value. No purely technical stories.

## Team Overrides
If the file `.roles/product_manager.md` exists in the project root, read it and follow those additional instructions.

## Pre-Checks

Before proceeding, verify the required inputs exist:

1. Check that the feature exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-feature $ARGUMENTS
```
If this fails, STOP and tell the user: "Feature not found. Run `/sdd-feature` first to create a feature specification."

2. Check that a workstream with a high_level_design.md exists:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" find-workstream $ARGUMENTS
```
If this fails, or if `<ws_feature_dir>/high_level_design.md` does not exist, STOP and tell the user: "No design found. Run `/sdd-design <feature-name>` first to create the high-level design."

## Setup

The feature and workstream paths were found during pre-checks. Use those paths for the rest of this skill.

## Objective
Decompose the feature into user stories with acceptance criteria.

## Context Gathering
Before generating stories, read the following files:
1. The feature spec: `specs/<feature_slug>/feature.md`
2. Global design docs: glob for `design/design.md` and `design/COMP_*.md`
3. The workstream design: `<ws_feature_dir>/high_level_design.md`
4. Any existing stories: glob for `specs/<feature_slug>/stories/STORY_*.md`

## Process
1. Read the feature specification and high-level design.
2. Identify natural increments of user value.
3. For each increment, write a user story with ACs.
4. Declare dependencies between stories via `depends_on`.
5. Verify each story requires no more than 3-5 tasks.

## Story File Schema

Frontmatter:
```yaml
---
id: "STORY_NNN"
title: "<story title>"
status: "TODO"
feature: "<FEAT_NNN>"
depends_on: []
acceptance_criteria:
  - id: "AC_NNN"
    description: "[Given <precondition>,] when <action>, then <expected result>"
    status: "TODO"
created: "<today's date YYYY-MM-DD>"
updated: "<today's date YYYY-MM-DD>"
---
```

Body:
```markdown
## User Story
As a [persona], I want [action], so that [benefit].

## Acceptance Criteria
- [ ] **AC_NNN**: [Given <precondition>,] when <action>, then <expected result>

## Technical Notes
[Optional. Non-binding observations for the Tech Lead.]
```

## Template
Read the template at `reference/story-template.md` and use it as the structural guide for each story file.

## Rules
- depends_on MUST only reference STORY IDs from the same feature.
- AC IDs use the format AC_NNN (e.g., AC_001, AC_002) scoped per story.

Determine the next story number:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" next-story-number <feature_dir_path>
```

## Output Location
Write files to: `specs/<feature_slug>/stories/STORY_NNN_<slug>.md`

## After Completion
Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

After regenerating the index, tell the user:

> **Next step:** Run `/sdd-tasks <feature-name>` to generate implementation tasks from these stories.
