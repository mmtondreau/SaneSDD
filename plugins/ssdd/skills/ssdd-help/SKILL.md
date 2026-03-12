---
name: ssdd-help
description: Display the SaneSDD workflow overview, available commands, and role system. Use when you need guidance on how to use SaneSDD.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: ""
---

# SaneSDD Help

Display the following information to the user. Do NOT read any files — just output this content directly.

---

## SaneSDD Workflow

SaneSDD (Sane Spec Driven Development) guides you through a structured, phased workflow. Each phase runs Claude as a different role with specific responsibilities.

### Quick Start

```
/ssdd-init                          # 1. Initialize project structure
/ssdd-feature                       # 2. Define a feature (interactive)
/ssdd-approve <file-path>           #    Review & approve individual files
/ssdd-design <feature-name>         # 3. Design the architecture (interactive)
/ssdd-approve <file-path>           #    Review & approve
/ssdd-stories <feature-name>        # 4. Generate user stories
/ssdd-approve <path1> <path2> ...   #    Review & approve each story
/ssdd-tasks <feature-name>          # 5. Generate implementation tasks
/ssdd-approve <path1> <path2> ...   #    Review & approve each task
/ssdd-plan <feature-name>           # 6. Create execution plan
/ssdd-approve <file-path>           #    Review & approve
/ssdd-implement <story-id>          # 7. Implement one story (on a branch)
/ssdd-merge <story-id>              # 8. Merge completed story to main
```

Repeat steps 7-8 for each story in the feature. Each command tells you what to run next when it completes. Use `/ssdd-approve` after each step to record your review before proceeding.

### Command Reference

| Command | Role | Mode | Description |
|---------|------|------|-------------|
| `/ssdd-init` | — | Auto | Create `.ssdd/specs/`, `.ssdd/work/`, `.ssdd/design/` directories and `INDEX.md` |
| `/ssdd-feature` | Product Manager | Interactive | Define a new feature specification |
| `/ssdd-design <name>` | System Architect | Interactive | Create high-level design, set up epic + domain components |
| `/ssdd-stories <name>` | Product Manager | Auto | Generate work stories with acceptance criteria (in epic) |
| `/ssdd-tasks <name>` | Tech Lead | Auto | Generate implementation tasks from work stories |
| `/ssdd-plan <name>` | Tech Lead | Auto | Create ordered execution plan |
| `/ssdd-implement <story>` | Multi-role | Auto | Implement one story: Developer → Code Review → Task QA → Story QA → Promote to Spec |
| `/ssdd-merge <story>` | — | Auto | Merge completed story branch to main after verification |
| `/ssdd-approve <file-path> [...]` | — | Auto | Mark individual artifact files as reviewed/approved |
| `/ssdd-status [name]` | — | Info | Show status of all epics, a specific epic, or a specific story |
| `/ssdd-help` | — | Info | Show this help |

**`<name>`** can be a feature ID (`FEAT_001`), slug (`checkout_resume`), or substring (`checkout`).

**`<story>`** can be a story ID (`STORY_001`), slug (`STORY_001_user_login`), or substring (`user_login`).

### Three Channels

**Spec Channel** — Living documentation of the system as it currently exists:
```
specs/
  THEME_NNN_slug/              — Groups related features
    features/
      FEAT_NNN_slug/           — Feature specification
        stories/               — Promoted stories (current system state)
```

**Work Channel** — Execution: planned changes being implemented:
```
work/
  EPIC_NNN_slug/               — Unit of planned change
    stories/
      STORY_NNN_slug/          — Work story with ACs
        TASK_NNN_slug.md       — Developer implementation unit
    high_level_design.md
    development_plan.yaml
```

**Design Channel** — Domain-driven architecture documentation:
```
design/
  design.md                    — System-wide architecture
  DOMAIN_NNN_slug/             — Bounded context
    COMP_slug.md               — Component within domain
```

- **specs/** is updated after implementation (stories promoted from work)
- **work/** is where active development happens (epics, stories, tasks)
- **design/** is updated after task completion

### Role System

| Role | What They Do | What They Don't Do |
|------|-------------|-------------------|
| **Product Manager** | Features, stories, ACs | No tasks, no code, no implementation details |
| **System Architect** | Design docs, component docs, ADRs | No stories, no tasks, no code |
| **Tech Lead** | Tasks, plans, AC coverage | No spec changes, no code |
| **Developer** | Code, tests, design doc updates | — |
| **Code Reviewer** | Review code quality, design adherence | No file modifications, no test execution |
| **Task QA** | Validate task done criteria | No file modifications |
| **Story QA** | Validate AC satisfaction | No file modifications |

### Implementation Flow (per story)

```
/ssdd-implement <story-id>
  └── Creates branch: story/STORY_NNN_slug
      └── For each task:
          ├── Developer implements
          ├── Code Reviewer reviews
          │   └── If rejected → back to Developer (with feedback)
          ├── Task QA validates
          │   └── If failed → back to Developer (with notes)
          └── Max 3 developer attempts per task
      └── Story QA validates all ACs
          └── If incomplete → Tech Lead creates remediation tasks → loop
/ssdd-merge <story-id>
  └── Verifies: story DONE, all tasks DONE, code review passed
  └── Merges story branch to main
```

### Acceptance Criteria Format

ACs use **Given-When-Then** format:
- Full: `Given <precondition>, when <action>, then <expected result>`
- Short: `When <action>, then <expected result>` (when precondition is obvious)

### Team Customization

Create `.roles/<rolename>.md` files to customize role behavior:
- `.roles/product_manager.md` — Affects `/ssdd-feature`, `/ssdd-stories`
- `.roles/system_architect.md` — Affects `/ssdd-design`
- `.roles/tech_lead.md` — Affects `/ssdd-tasks`, `/ssdd-plan`
- `.roles/developer.md` — Affects `/ssdd-implement` (dev phase)
- `.roles/code_reviewer.md` — Affects `/ssdd-implement` (code review phase)
- `.roles/task_qa.md` — Affects `/ssdd-implement` (QA phase)
- `.roles/story_qa.md` — Affects `/ssdd-implement` (QA phase)

### Approval Workflow

After each step, SaneSDD asks you to review the generated artifacts. Use `/ssdd-approve` to record your review on individual files:

```
/ssdd-approve .ssdd/specs/THEME_001_checkout/features/FEAT_001_checkout/feature.md
/ssdd-approve .ssdd/work/EPIC_001_checkout/high_level_design.md
/ssdd-approve .ssdd/work/EPIC_001_checkout/stories/STORY_001/story.md .ssdd/work/EPIC_001_checkout/stories/STORY_002/story.md
/ssdd-approve .ssdd/work/EPIC_001_checkout/development_plan.yaml
```

You can approve multiple files in a single command. Each file's `approved` frontmatter field will be set to today's date.

If you proceed to the next step without approving, SaneSDD will warn you and list the unapproved artifacts. You can choose to continue anyway or go back and approve first.

### Tips

- **Per-story workflow:** `/ssdd-implement` processes one story at a time. Run it for each story, then `/ssdd-merge` to merge.
- **Branching:** Each story runs on its own `story/STORY_NNN_slug` branch. Use `/ssdd-merge` to merge back to main.
- **Resumability:** `/ssdd-implement` skips DONE tasks. Safe to re-run for the same story.
- **INDEX.md:** Auto-generated after each command. Check it for project status.
- **Epics:** Running `/ssdd-design` creates an epic in `.ssdd/work/`. Each epic is an independent unit of change.
- **Promotion:** When a work story passes Story QA, it is automatically promoted to the spec channel as living documentation.
- **Pre-checks:** Each command validates its inputs and tells you what to run first if something is missing.
- **Approval gates:** Each command checks if the prior step's artifacts have been approved. You can skip approval, but SaneSDD will warn you.
