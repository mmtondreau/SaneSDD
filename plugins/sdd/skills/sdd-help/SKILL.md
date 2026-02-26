---
name: sdd-help
description: Display the SDD workflow overview, available commands, and role system. Use when you need guidance on how to use SDD.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: ""
---

# SDD Help

Display the following information to the user. Do NOT read any files — just output this content directly.

---

## SDD Workflow

SDD (Spec Driven Development) guides you through a structured, phased workflow. Each phase runs Claude as a different role with specific responsibilities.

### Quick Start

```
/sdd-init                          # 1. Initialize project structure
/sdd-feature                       # 2. Define a feature (interactive)
/sdd-design <feature-name>         # 3. Design the architecture (interactive)
/sdd-stories <feature-name>        # 4. Generate user stories
/sdd-tasks <feature-name>          # 5. Generate implementation tasks
/sdd-plan <feature-name>           # 6. Create execution plan
/sdd-implement <feature-name>      # 7. Implement with QA loop
```

Each command tells you what to run next when it completes.

### Command Reference

| Command | Role | Mode | Description |
|---------|------|------|-------------|
| `/sdd-init` | — | Auto | Create `specs/`, `work/`, `design/` directories and `INDEX.md` |
| `/sdd-feature` | Product Manager | Interactive | Define a new feature specification |
| `/sdd-design <name>` | System Architect | Interactive | Create high-level design + component docs |
| `/sdd-stories <name>` | Product Manager | Auto | Generate user stories with acceptance criteria |
| `/sdd-tasks <name>` | Tech Lead | Auto | Generate implementation tasks from stories |
| `/sdd-plan <name>` | Tech Lead | Auto | Create ordered execution plan |
| `/sdd-implement <name>` | Multi-role | Auto | Implement: Developer → Task QA → Story QA → Remediation |
| `/sdd-help` | — | Info | Show this help |

**`<name>`** can be a feature ID (`FEAT_001`), slug (`checkout_resume`), or substring (`checkout`).

### Artifact Hierarchy

```
Feature (FEAT_NNN)           — What to build (owned by Product Manager)
  └── Story (STORY_NNN)      — User-facing behavior with ACs
        └── Task (TASK_NNN)   — Developer implementation unit (lives in work/)
```

- **specs/** holds features and stories (source of truth, persists across workstreams)
- **work/** holds designs, tasks, and plans (scoped to a workstream)
- **design/** holds global architecture and component docs

### Role System

| Role | What They Do | What They Don't Do |
|------|-------------|-------------------|
| **Product Manager** | Features, stories, ACs | No tasks, no code, no implementation details |
| **System Architect** | Design docs, component docs, ADRs | No stories, no tasks, no code |
| **Tech Lead** | Tasks, plans, AC coverage | No spec changes, no code |
| **Developer** | Code, tests, design doc updates | — |
| **Task QA** | Validate task done criteria | No file modifications |
| **Story QA** | Validate AC satisfaction | No file modifications |

### Acceptance Criteria Format

ACs use **Given-When-Then** format:
- Full: `Given <precondition>, when <action>, then <expected result>`
- Short: `When <action>, then <expected result>` (when precondition is obvious)

### Team Customization

Create `.roles/<rolename>.md` files to customize role behavior:
- `.roles/product_manager.md` — Affects `/sdd-feature`, `/sdd-stories`
- `.roles/system_architect.md` — Affects `/sdd-design`
- `.roles/tech_lead.md` — Affects `/sdd-tasks`, `/sdd-plan`
- `.roles/developer.md` — Affects `/sdd-implement` (dev phase)
- `.roles/task_qa.md` — Affects `/sdd-implement` (QA phase)
- `.roles/story_qa.md` — Affects `/sdd-implement` (QA phase)

### Tips

- **Resumability:** `/sdd-implement` skips DONE stories/tasks. Safe to re-run.
- **INDEX.md:** Auto-generated after each command. Check it for project status.
- **Workstreams:** Running `/sdd-design` again creates a new workstream (WS_002, etc.) instead of overwriting.
- **Pre-checks:** Each command validates its inputs and tells you what to run first if something is missing.
