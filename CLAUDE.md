# SDD (Spec Driven Development) — Project Instructions

These instructions apply to EVERY role and EVERY phase.

## Utility CLI

SDD includes `sdd-util`, a Python CLI for deterministic state operations.
Skills invoke it via `"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh"`.

Available commands:
- `sdd-util init [--path DIR]` — initialize specs/, work/, design/ directories and INDEX.md
- `sdd-util next-theme-number` — prints the next THEME_NNN number
- `sdd-util next-feature-number` — prints the next FEAT_NNN number
- `sdd-util next-feature-number-in-theme <theme_dir>` — prints next FEAT_NNN number within a theme
- `sdd-util next-story-number <feature_dir>` — prints next STORY_NNN number
- `sdd-util next-task-number <epic_story_dir>` — prints next TASK_NNN number
- `sdd-util next-epic-number` — prints the next EPIC_NNN number
- `sdd-util next-domain-number` — prints the next DOMAIN_NNN number
- `sdd-util find-theme <name>` — prints the theme directory path
- `sdd-util find-feature <name>` — prints the feature directory path (searches under specs/THEME_*/features/)
- `sdd-util find-story <name> [--channel spec|work|both]` — prints story location as JSON (default: both channels)
- `sdd-util find-epic <name>` — prints the epic directory path
- `sdd-util find-domain <name>` — prints the domain directory path
- `sdd-util create-epic <epic_slug>` — creates and prints new epic path under work/
- `sdd-util regenerate-index` — regenerates INDEX.md
- `sdd-util plan-json <epic_name>` — outputs development plan as JSON
- `sdd-util promote-story <work_story_path> --epic <epic_dir>` — promotes a completed work story to the spec channel
- `sdd-util context-path <role> --epic <epic_dir>` or `--theme <theme_dir>` — prints the agent context file path for a role
- `sdd-util read-context <role> --epic <epic_dir>` or `--theme <theme_dir>` — prints the agent context file contents (empty if not found)
- `sdd-util status [name] [--type epic|story]` — shows status of an epic, story, or all epics (auto-detects type if omitted)

## Sub-Agent Architecture

Each skill acts as a **thin orchestrator** that dispatches work to a Task tool sub-agent. This keeps the main conversation context clean. Agent context is persisted between invocations:

- **Context path**: `work/EPIC_NNN_slug/agent/<role>/context.md` (or `specs/THEME_NNN_slug/agent/<role>/context.md` for pre-epic skills)
- **Import**: At the start of each skill, prior context is read via `sdd-util read-context`
- **Export**: Each sub-agent writes a context summary as its final step
- **Roles**: product_manager, system_architect, tech_lead, developer, code_reviewer, task_qa, story_qa

## Foundational Principles

1. **Three channels separate concerns.** The **Spec** channel is living documentation describing the system as it currently exists. The **Work** channel is for planning and executing changes. The **Design** channel captures domain-driven architecture. Specs are updated via promotion after implementation completes — never during development.

2. **Specifications are the source of truth.** All work traces back to a spec. Code without a backing task is unauthorized. A task without a backing story is unauthorized. A story without a backing feature is unauthorized.

3. **IDs are immutable.** Once assigned, THEME_NNN, FEAT_NNN, EPIC_NNN, STORY_NNN, TASK_NNN, DOMAIN_NNN, and AC_NNN identifiers never change. They are never reused or renumbered. If an artifact is deleted, its ID is retired.

4. **Work stories are promoted to specs.** After implementation completes and Story QA passes, work stories are promoted to the spec channel as living documentation. Work stories are kept as history.

5. **Dependencies are explicit.** The `depends_on` field in YAML frontmatter is the sole mechanism for declaring ordering constraints.

6. **Status transitions are linear.**
   - Themes: TODO → IN_PROGRESS → DONE
   - Features: TODO → IN_PROGRESS → DONE
   - Epics: TODO → IN_PROGRESS → DONE
   - Stories: TODO → IN_PROGRESS → DONE (or BLOCKED at any point)
   - Tasks: TODO → IN_PROGRESS → DONE (or BLOCKED at any point)

## File Layout

```
# Spec channel — living documentation (current system state)
specs/THEME_NNN_slug/theme.md                              Theme grouping
specs/THEME_NNN_slug/features/FEAT_NNN_slug/feature.md     Feature specification
specs/THEME_NNN_slug/features/FEAT_NNN_slug/stories/STORY_NNN_slug.md  Spec story (promoted from work)

# Work channel — execution (planned changes)
work/EPIC_NNN_slug/epic.md                                 Epic definition
work/EPIC_NNN_slug/high_level_design.md                    Epic-level design
work/EPIC_NNN_slug/development_plan.yaml                   Development plan
work/EPIC_NNN_slug/stories/STORY_NNN/story.md              Work story (with ACs)
work/EPIC_NNN_slug/stories/STORY_NNN/TASK_NNN_slug.md      Task
work/EPIC_NNN_slug/agent/<role>/context.md                 Agent context persistence

# Design channel — domain-driven architecture
design/design.md                                           Top-level system architecture
design/DOMAIN_NNN_slug/domain.md                           Bounded context description
design/DOMAIN_NNN_slug/COMP_slug.md                        Component within domain

# Other
INDEX.md                                                   File index (auto-generated)
.roles/*.md                                                Team-specific role overrides
```

## Frontmatter Contract

All spec files MUST begin with YAML frontmatter delimited by `---`.

### Theme frontmatter
```yaml
---
id: "THEME_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Feature frontmatter
```yaml
---
id: "FEAT_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE
theme: "THEME_NNN"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Spec story frontmatter
```yaml
---
id: "STORY_NNN"
title: "<title>"
status: DONE
feature: "FEAT_NNN"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Epic frontmatter
```yaml
---
id: "EPIC_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE
spec_theme: "THEME_NNN"      # optional cross-channel ref
spec_feature: "FEAT_NNN"     # optional cross-channel ref
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Work story frontmatter
```yaml
---
id: "STORY_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE | BLOCKED
epic: "EPIC_NNN"
spec_feature: "FEAT_NNN"     # optional: which spec feature to promote to
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
code_review: "APPROVED | CHANGES_REQUESTED"  # optional, set by code reviewer
review_notes: "<feedback>"                     # optional, set by code reviewer when requesting changes
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Domain frontmatter
```yaml
---
domain: "<DomainName>"
id: "DOMAIN_NNN"
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
