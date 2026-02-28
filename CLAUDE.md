# SDD (Spec Driven Development) — Project Instructions

These instructions apply to EVERY role and EVERY phase.

## Utility CLI

SDD includes `sdd-util`, a Python CLI for deterministic state operations.
Skills invoke it via `"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh"`.

Available commands:
- `sdd-util init [--path DIR]` — initialize specs/, work/, design/ directories and INDEX.md
- `sdd-util next-feature-number` — prints the next FEAT_NNN number
- `sdd-util next-story-number <feature_dir>` — prints next STORY_NNN number
- `sdd-util next-task-number <ws_story_dir>` — prints next TASK_NNN number
- `sdd-util find-feature <name>` — prints the feature directory path
- `sdd-util find-workstream <feature_name>` — prints the active workstream path
- `sdd-util create-workstream <feature_slug>` — creates and prints new workstream path
- `sdd-util regenerate-index` — regenerates INDEX.md
- `sdd-util plan-json <feature_name>` — outputs development plan as JSON
- `sdd-util context-path <role> --workstream <ws_feat_dir>` or `--feature <feat_dir>` — prints the agent context file path for a role
- `sdd-util read-context <role> --workstream <ws_feat_dir>` or `--feature <feat_dir>` — prints the agent context file contents (empty if not found)

## Sub-Agent Architecture

Each skill acts as a **thin orchestrator** that dispatches work to a Task tool sub-agent. This keeps the main conversation context clean. Agent context is persisted between invocations:

- **Context path**: `work/WS_NNN/FEAT_NNN_slug/agent/<role>/context.md` (or `specs/FEAT_NNN_slug/agent/<role>/context.md` for pre-workstream skills)
- **Import**: At the start of each skill, prior context is read via `sdd-util read-context`
- **Export**: Each sub-agent writes a context summary as its final step
- **Roles**: product_manager, system_architect, tech_lead, developer, task_qa, story_qa

## Foundational Principles

1. **Specifications are the source of truth.** All work traces back to a spec. Code without a backing task is unauthorized. A task without a backing story is unauthorized. A story without a backing feature is unauthorized.

2. **IDs are immutable.** Once assigned, FEAT_NNN, STORY_NNN, TASK_NNN, and AC_NNN identifiers never change. They are never reused or renumbered. If an artifact is deleted, its ID is retired.

3. **Dependencies are explicit.** The `depends_on` field in YAML frontmatter is the sole mechanism for declaring ordering constraints.

4. **Status transitions are linear.**
   - Features: TODO → IN_PROGRESS → DONE
   - Stories: TODO → IN_PROGRESS → DONE (or BLOCKED at any point)
   - Tasks: TODO → IN_PROGRESS → DONE (or BLOCKED at any point)

## File Layout

```
specs/FEAT_NNN_slug/feature.md          Feature specifications
specs/FEAT_NNN_slug/stories/STORY_NNN_slug.md  User stories
work/WS_NNN/FEAT_NNN_slug/high_level_design.md  Workstream design
work/WS_NNN/FEAT_NNN_slug/development_plan.yaml  Dev plan
work/WS_NNN/FEAT_NNN_slug/stories/STORY_NNN/TASK_NNN_slug.md  Tasks
work/WS_NNN/FEAT_NNN_slug/agent/<role>/context.md  Agent context persistence
design/design.md                        High-level architecture (global)
design/COMP_*.md                        Component design documents (global)
INDEX.md                                File index (auto-generated)
.roles/*.md                             Team-specific role overrides
```

## Frontmatter Contract

All spec files MUST begin with YAML frontmatter delimited by `---`.

### Feature frontmatter
```yaml
---
id: "FEAT_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Story frontmatter
```yaml
---
id: "STORY_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE | BLOCKED
feature: "FEAT_NNN"
depends_on: []
acceptance_criteria:
  - id: "AC_NNN"
    description: "<testable criterion>"
    status: "TODO"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Task frontmatter
```yaml
---
id: "TASK_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE | BLOCKED
story: "STORY_NNN"
depends_on: []
ac_mapping: ["AC_NNN"]
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

## Cross-Referencing

- Always reference artifacts by ID, never by title.
- Titles may change. IDs must not.

## Error Handling

- If you detect a conflict between two specs, STOP and flag the conflict.
- If a required file is missing, STOP and report it.
- If a dependency is unmet, set the artifact's status to BLOCKED.

## Team Overrides

If a file `.roles/<rolename>.md` exists, read and follow its instructions in addition to the skill-specific instructions. The role name for each skill is noted in the skill's instructions.
