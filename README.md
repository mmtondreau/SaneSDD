# SDD - Spec Driven Development

A Claude Code plugin that orchestrates Claude through a phased, spec-driven development workflow. SDD maintains a living `specs/` folder as the single source of truth for requirements and a `work/` directory for execution artifacts. Each phase runs Claude as a different role (Product Manager, System Architect, Tech Lead, Developer, Story QA, Task QA) with role-specific instructions and tool restrictions.

SDD is distributed as a [Claude Code plugin](https://docs.anthropic.com/en/docs/claude-code/skills) and backed by a thin Python utility CLI for deterministic state operations.

## Table of Contents

- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Setup](#project-setup)
- [Core Concepts](#core-concepts)
- [Slash Commands](#slash-commands)
  - [/sdd-help](#sdd-help)
  - [/sdd-init](#sdd-init)
  - [/sdd-feature](#sdd-feature)
  - [/sdd-design](#sdd-design)
  - [/sdd-stories](#sdd-stories)
  - [/sdd-tasks](#sdd-tasks)
  - [/sdd-plan](#sdd-plan)
  - [/sdd-implement](#sdd-implement)
- [Typical User Workflow](#typical-user-workflow)
- [Directory Layout](#directory-layout)
- [Frontmatter Contracts](#frontmatter-contracts)
- [Role System](#role-system)
- [Team Customization](#team-customization)
- [Resumability](#resumability)
- [Development](#development)

---

## Quick Start

```
/sdd-init                          # Initialize project structure
/sdd-feature                       # Define a feature (interactive)
/sdd-design <feature-name>         # Design the architecture (interactive)
/sdd-stories <feature-name>        # Generate user stories
/sdd-tasks <feature-name>          # Generate implementation tasks
/sdd-plan <feature-name>           # Create execution plan
/sdd-implement <feature-name>      # Implement with QA loop
```

Each command tells you what to run next when it completes. Run `/sdd-help` at any time for a full workflow overview.

---

## Requirements

- **Python 3.10+** (with pip)
- **Claude Code** - [Installation guide](https://docs.anthropic.com/en/docs/claude-code/overview)

No API key is required — SDD runs entirely within Claude Code.

## Installation

SDD is distributed as a Claude Code plugin marketplace. Add it from within a Claude Code session:

```
/plugin marketplace add /path/to/sdd
# or from a git repository:
/plugin marketplace add https://github.com/your-org/sdd.git
```

Then install the SDD plugin:

```
/plugin install sdd@sdd-marketplace
```

### First-time Setup

Dependencies are installed automatically on first use. If you prefer to install them ahead of time, run:

```bash
/path/to/sdd/plugins/sdd/scripts/setup.sh
```

This installs the Python CLI dependencies locally within the plugin directory using pip.

### Development Installation

If you're working on SDD itself:

```bash
git clone <repository-url>
cd sdd
poetry install
poetry run sdd-util --help
```

---

## Project Setup

Initialize a new SDD project from within Claude Code:

```
/sdd-init
```

This creates the required directory structure and generates an initial `INDEX.md`:

```
your-project/
  specs/          # Feature specifications live here
  work/           # Workstreams and execution artifacts
  design/         # Architecture and component documents
  INDEX.md        # Auto-generated project index
```

Running init is idempotent — it's safe to run again and will only create directories that don't already exist.

### Optional Setup

```bash
# Create team-specific role overrides
mkdir .roles

# Customize how the Product Manager role behaves on your project
echo "# Custom PM Rules
Include performance criteria for data-fetching stories.
Maximum 5 ACs per story." > .roles/product_manager.md
```

---

## Core Concepts

### Hierarchy

SDD enforces a strict hierarchy of artifacts:

```
Feature (epic)
  └── User Story (with Acceptance Criteria)
        └── Task (implementation unit, lives in work/)
```

- **Features** define _what_ to build (owned by Product Manager)
- **Stories** break features into user-facing behaviors with testable ACs
- **Tasks** are developer-level implementation units mapped to specific ACs
- Every artifact has a unique, immutable ID (e.g., `FEAT_001`, `STORY_003`, `TASK_002`, `AC_005`)

### Status Lifecycle

All artifacts follow linear status transitions:

| Artifact | Transitions |
|----------|------------|
| Feature  | `TODO` → `IN_PROGRESS` → `DONE` |
| Story    | `TODO` → `IN_PROGRESS` → `DONE` (or `BLOCKED`) |
| Task     | `TODO` → `IN_PROGRESS` → `DONE` (or `BLOCKED`) |

### Acceptance Criteria Format

All acceptance criteria use **Given-When-Then** format:

- **Full format:** `Given <precondition>, when <action>, then <expected result>`
- **Short format:** `When <action>, then <expected result>` (when the precondition is obvious)

Examples:
- `Given a user with items in their cart, when they log out, then the cart is persisted to the database`
- `When the user clicks "Resume Cart", then all previously saved items are restored`

### Specs vs Work

- **`specs/`** contains the _requirements_: features and stories. These are the source of truth and persist across workstreams.
- **`work/`** contains _execution artifacts_: designs, tasks, development plans. These are scoped to a workstream and can be regenerated.
- **`design/`** contains _global architecture_: system-level design and component design docs. Updated across features.
- Tasks live **only** in `work/`, never in `specs/`.

---

## Slash Commands

All commands are invoked from within a Claude Code session. SDD auto-detects the project root by walking up from the current directory looking for a `specs/` directory or `.git/` folder.

Each command validates its required inputs before starting. If something is missing, it tells you exactly what to run first.

### `/sdd-help`

Displays the SDD workflow overview, all available commands, the role system, and tips for using SDD effectively.

```
/sdd-help
```

No prerequisites. Run this at any time.

---

### `/sdd-init`

Initializes a new SDD project by creating the required directory structure.

```
/sdd-init
/sdd-init /path/to/project
```

**What happens:**
1. Creates `specs/`, `work/`, and `design/` directories (skips any that already exist)
2. Generates an initial `INDEX.md`

**Next step:** `/sdd-feature`

---

### `/sdd-feature`

**Role:** Product Manager | **Mode:** Interactive | **Prerequisite:** `/sdd-init`

Starts an interactive session with Claude acting as a Product Manager to define a new feature specification.

```
/sdd-feature
/sdd-feature a checkout system that saves cart state
```

**What happens:**
1. Determines the next available feature number (e.g., `FEAT_001`)
2. Claude helps you articulate the feature, asking clarifying questions
3. Produces `specs/FEAT_NNN_slug/feature.md` with YAML frontmatter

**Output file example** (`specs/FEAT_001_checkout_resume/feature.md`):
```markdown
---
id: "FEAT_001"
title: "Checkout Resume"
status: "TODO"
created: "2026-02-23"
updated: "2026-02-23"
---

## Problem Statement
Users lose their cart contents when they leave the site...

## Success Criteria
- Cart persistence rate > 95%
- Resume-to-purchase conversion > 30%
```

**Next step:** `/sdd-design <feature-name>`

---

### `/sdd-design`

**Role:** System Architect | **Mode:** Interactive | **Prerequisite:** `/sdd-feature`

Creates a high-level design document for a feature, along with detailed component design docs.

```
/sdd-design FEAT_001
/sdd-design checkout
```

**Arguments:** Feature ID or name substring (e.g., `FEAT_001_checkout_resume`, `FEAT_001`, or `checkout`)

**What happens:**
1. Looks up the feature in `specs/`
2. Creates a new workstream (`work/WS_NNN/FEAT_NNN_slug/`)
3. Claude discusses architecture interactively, then writes the design
4. Produces `work/WS_NNN/FEAT_NNN_slug/high_level_design.md`
5. Creates or updates `design/COMP_<name>.md` for each component with full detail
6. Updates `design/design.md` with the system-wide architecture view

**Next step:** `/sdd-stories <feature-name>`

---

### `/sdd-stories`

**Role:** Product Manager | **Mode:** Automated | **Prerequisite:** `/sdd-design`

Generates user stories from the feature spec and design documents.

```
/sdd-stories FEAT_001
/sdd-stories checkout
```

**Arguments:** Feature ID or name substring

**What happens:**
1. Reads the feature spec and high-level design
2. Claude generates story files with YAML frontmatter and acceptance criteria (in Given-When-Then format)
3. Produces `specs/FEAT_NNN_slug/stories/STORY_NNN_slug.md` files

**Output file example** (`specs/FEAT_001_checkout_resume/stories/STORY_001_save_cart.md`):
```markdown
---
id: "STORY_001"
title: "Save Cart"
status: "TODO"
feature: "FEAT_001"
depends_on: []
acceptance_criteria:
  - id: "AC_001"
    description: "Given a user with items in their cart, when they log out, then the cart items are persisted"
    status: "TODO"
  - id: "AC_002"
    description: "When the user logs back in, then their previously saved cart is restored"
    status: "TODO"
created: "2026-02-23"
updated: "2026-02-23"
---

## User Story
As a shopper, I want my cart to be saved when I leave,
so that I can resume shopping later.

## Acceptance Criteria
- [ ] **AC_001**: Given a user with items in their cart, when they log out, then the cart items are persisted
- [ ] **AC_002**: When the user logs back in, then their previously saved cart is restored
```

**Next step:** `/sdd-tasks <feature-name>`

---

### `/sdd-tasks`

**Role:** Tech Lead | **Mode:** Automated | **Prerequisite:** `/sdd-stories`

Generates implementation tasks from stories and design documents.

```
/sdd-tasks FEAT_001
/sdd-tasks checkout
```

**Arguments:** Feature ID or name substring

**What happens:**
1. Reads stories, feature spec, and design docs
2. Claude generates task files mapped to specific ACs
3. Produces `work/WS_NNN/FEAT_NNN_slug/stories/STORY_NNN/TASK_NNN_slug.md` files

**Next step:** `/sdd-plan <feature-name>`

---

### `/sdd-plan`

**Role:** Tech Lead | **Mode:** Automated | **Prerequisite:** `/sdd-tasks`

Generates a `development_plan.yaml` that defines the execution order for all stories and tasks.

```
/sdd-plan FEAT_001
/sdd-plan checkout
```

**Arguments:** Feature ID or name substring

**What happens:**
1. Reads all stories and tasks
2. Claude produces an ordered execution plan respecting dependencies
3. Produces `work/WS_NNN/FEAT_NNN_slug/development_plan.yaml`

**Output file example** (`development_plan.yaml`):
```yaml
feature: "FEAT_001_checkout_resume"
generated_at: "2026-02-23T10:00:00"
stories:
  - story_id: "STORY_001"
    order: 1
    tasks:
      - task_id: "TASK_001"
        order: 1
        depends_on: []
        estimated_effort: "medium"
      - task_id: "TASK_002"
        order: 2
        depends_on: ["TASK_001"]
        estimated_effort: "small"
  - story_id: "STORY_002"
    order: 2
    tasks:
      - task_id: "TASK_001"
        order: 1
risks:
  - description: "Cart merge logic may be complex"
    severity: "medium"
    mitigation: "Start with simple last-write-wins strategy"
```

**Next step:** `/sdd-implement <feature-name>`

---

### `/sdd-implement`

**Role:** Developer, Task QA, Story QA, Tech Lead | **Mode:** Automated multi-role loop | **Prerequisite:** `/sdd-plan`

Executes the full implementation loop, cycling through multiple roles automatically.

```
/sdd-implement FEAT_001
/sdd-implement checkout STORY_001
```

**Arguments:**
- First argument (required): Feature ID or name substring
- Second argument (optional): Story filter to implement only a specific story

**What happens for each story (in plan order):**

```
Story marked IN_PROGRESS
│
├── For each task:
│   ├── [Attempt 1..3]:
│   │   ├── DEVELOPER: Implements the code
│   │   ├── TASK QA: Validates implementation, runs tests
│   │   └── Check task status:
│   │       ├── DONE → move to next task
│   │       └── Not DONE → retry (up to 3 attempts)
│   └── After 3 failures → mark task BLOCKED
│
├── STORY QA: Validates all acceptance criteria, runs tests
│   ├── All ACs DONE → mark story DONE
│   └── Incomplete ACs → TECH LEAD creates remediation tasks
│
└── Next story
```

---

## Typical User Workflow

Here is the complete end-to-end workflow for building a feature:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  /sdd-init  │ ──▶ │ /sdd-feature │ ──▶ │ /sdd-design  │
│  (one-time) │     │   (PM, int.) │     │ (Arch, int.) │
└─────────────┘     └──────────────┘     └──────────────┘
                                                │
                    ┌──────────────┐     ┌───────┴──────┐
                    │ /sdd-tasks   │ ◀── │ /sdd-stories │
                    │  (TL, auto)  │     │  (PM, auto)  │
                    └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐     ┌───────────────┐
                    │  /sdd-plan   │ ──▶ │/sdd-implement │
                    │  (TL, auto)  │     │ (multi-role)  │
                    └──────────────┘     └───────────────┘
```

### Step 0: Initialize the Project

```
/sdd-init
```

Creates the `specs/`, `work/`, and `design/` directories. Only needed once per project.

### Step 1: Define the Feature

```
/sdd-feature
```

Interactive session. Describe what you want to build. Claude (as Product Manager) asks clarifying questions and writes a structured feature spec with success criteria.

### Step 2: Create the Design

```
/sdd-design checkout_resume
```

Interactive session. Claude (as System Architect) reads the feature spec, discusses architecture with you, and produces:
- A workstream-scoped `high_level_design.md`
- Detailed `design/COMP_<name>.md` for each component
- An updated `design/design.md` with the system-wide view

### Step 3: Generate Stories

```
/sdd-stories checkout_resume
```

Automated. Claude (as Product Manager) breaks the feature into user stories with Given-When-Then acceptance criteria.

### Step 4: Generate Tasks

```
/sdd-tasks checkout_resume
```

Automated. Claude (as Tech Lead) creates implementation tasks from the stories, each mapped to specific ACs. Verifies complete AC coverage.

### Step 5: Create the Plan

```
/sdd-plan checkout_resume
```

Automated. Claude (as Tech Lead) orders all tasks respecting dependencies into an execution plan with effort estimates and risk assessment.

### Step 6: Implement

```
/sdd-implement checkout_resume
```

Automated multi-role loop. For each story in plan order, Claude cycles through:
1. **Developer** — writes code and tests
2. **Task QA** — validates done criteria, runs tests, checks coverage
3. **Story QA** — validates all ACs are satisfied
4. **Tech Lead** — creates remediation tasks for any gaps

### Checking Progress

After each command, `INDEX.md` is automatically regenerated. Open it to see the current state of all features, workstreams, and design documents.

---

## Directory Layout

After running through the full workflow, your project will look like this:

```
your-project/
├── specs/                                    # Source of truth (requirements)
│   └── FEAT_001_checkout_resume/
│       ├── feature.md                        # Feature specification
│       └── stories/
│           ├── STORY_001_save_cart.md         # User story with ACs
│           └── STORY_002_guest_checkout.md
│
├── work/                                     # Execution artifacts
│   └── WS_001/                               # Workstream
│       └── FEAT_001_checkout_resume/
│           ├── high_level_design.md           # Architecture design
│           ├── development_plan.yaml          # Execution plan
│           └── stories/
│               ├── STORY_001/
│               │   ├── TASK_001_create_cart_session_table.md
│               │   └── TASK_002_add_merge_endpoint.md
│               └── STORY_002/
│                   └── TASK_001_allow_guest_checkout.md
│
├── design/                                   # Global architecture docs
│   ├── design.md                             # System-wide architecture
│   ├── COMP_cart.md                          # Component design: Cart
│   └── COMP_session.md                       # Component design: Session
│
├── CLAUDE.md                                 # Global SDD instructions (from plugin)
├── INDEX.md                                  # Auto-generated file index
│
└── .roles/                                   # Optional team overrides
    ├── product_manager.md
    └── developer.md
```

The SDD repository itself is structured as a plugin marketplace:

```
sdd/                                          # Marketplace repository
├── .claude-plugin/
│   └── marketplace.json                      # Marketplace catalog
├── plugins/
│   └── sdd/                                  # The SDD plugin
│       ├── .claude-plugin/plugin.json        # Plugin manifest
│       ├── CLAUDE.md                         # Global SDD instructions
│       ├── skills/                           # Slash command definitions
│       │   ├── sdd-help/SKILL.md
│       │   ├── sdd-init/SKILL.md
│       │   ├── sdd-feature/
│       │   │   ├── SKILL.md
│       │   │   └── reference/
│       │   │       └── feature-template.md
│       │   ├── sdd-design/
│       │   │   ├── SKILL.md
│       │   │   └── reference/
│       │   │       ├── high-level-design-template.md
│       │   │       └── component-design-template.md
│       │   ├── sdd-stories/
│       │   │   ├── SKILL.md
│       │   │   └── reference/
│       │   │       └── story-template.md
│       │   ├── sdd-tasks/
│       │   │   ├── SKILL.md
│       │   │   └── reference/
│       │   │       └── task-template.md
│       │   ├── sdd-plan/
│       │   │   ├── SKILL.md
│       │   │   └── reference/
│       │   │       └── development-plan-template.yaml
│       │   └── sdd-implement/
│       │       ├── SKILL.md
│       │       └── reference/
│       │           ├── role-profiles.md
│       │           └── implementation-loop.md
│       └── scripts/
│           ├── setup.sh                      # Dependency installer
│           └── sdd-util.sh                   # Utility CLI wrapper
├── src/sdd/                                  # Utility CLI (sdd-util)
│   ├── config.py
│   ├── state.py
│   ├── workstream.py
│   ├── plan_parser.py
│   ├── index_manager.py
│   └── util_cli.py
└── pyproject.toml                            # Python dependencies
```

### Key Directories (in your project)

| Directory | Purpose | Managed By |
|-----------|---------|------------|
| `specs/` | Feature specs and stories (source of truth) | Product Manager |
| `work/` | Workstreams, designs, tasks, plans | System Architect, Tech Lead, Developer |
| `design/` | Global architecture and component docs | System Architect |
| `.roles/` | Team-specific role customizations | You (manual) |

---

## Frontmatter Contracts

All spec files use YAML frontmatter (delimited by `---`) as structured metadata. Claude reads and writes this frontmatter to track state.

### Feature Frontmatter

```yaml
---
id: "FEAT_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Story Frontmatter

```yaml
---
id: "STORY_NNN"
title: "<title>"
status: TODO | IN_PROGRESS | DONE | BLOCKED
feature: "FEAT_NNN"
depends_on: []
acceptance_criteria:
  - id: "AC_NNN"
    description: "[Given <precondition>,] when <action>, then <expected result>"
    status: "TODO"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Task Frontmatter

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

### Component Design Frontmatter

```yaml
---
component: "<ComponentName>"
depends_on: []
stories: []
updated: "YYYY-MM-DD"
---
```

### Rules

- **IDs are immutable.** Once assigned, they never change or get reused.
- **Status transitions are linear.** No skipping states (except to BLOCKED).
- **Cross-references use IDs, not titles.** Titles can change; IDs cannot.
- **AC IDs are scoped per story.** `AC_001` in STORY_001 is different from `AC_001` in STORY_002.
- **ACs use Given-When-Then format.** `Given` may be omitted when the precondition is obvious.

---

## Role System

SDD assigns Claude a specific role for each phase, controlling its behavior through skill instructions and tool restrictions.

| Role | Slash Commands | Allowed Tools |
|------|---------------|---------------|
| **Product Manager** | `/sdd-feature`, `/sdd-stories` | Read, Write, Edit, Glob, Grep, Bash |
| **System Architect** | `/sdd-design` | Read, Write, Edit, Glob, Grep, Bash |
| **Tech Lead** | `/sdd-tasks`, `/sdd-plan`, remediation | Read, Write, Edit, Glob, Grep, Bash |
| **Developer** | `/sdd-implement` (dev phase) | Read, Write, Edit, Glob, Grep, Bash |
| **Task QA** | `/sdd-implement` (QA phase) | Read-only + Bash (no Write/Edit) |
| **Story QA** | `/sdd-implement` (QA phase) | Read-only + Bash (no Write/Edit) |

### What the Restrictions Mean

- **Product Manager / Architect / Tech Lead** focus on spec and design artifacts. Their skill instructions constrain them from writing implementation code.
- **Developer** has full access including Bash, enabling code compilation, test runs, and file manipulation.
- **QA roles** are instructed to be read-only during their phases (only updating frontmatter status). They run tests via Bash but do not modify source code.

---

## Team Customization

You can customize how each role behaves on your project by creating override files in `.roles/`:

```bash
mkdir -p .roles
```

### Example: Custom Product Manager

`.roles/product_manager.md`:
```markdown
# Product Manager Overrides

## Story Format
- Include performance criteria for any data-fetching story
- Maximum 5 ACs per story

## Naming Conventions
- Story slugs must use snake_case
- Feature slugs must start with a verb (e.g., add_checkout, improve_search)
```

### Example: Custom Developer

`.roles/developer.md`:
```markdown
# Developer Overrides

## Code Standards
- Use TypeScript strict mode
- All functions must have JSDoc comments
- Tests must use Vitest, not Jest
- Follow the repository's existing patterns in src/

## Architecture Rules
- Use the repository pattern for data access
- All API endpoints must have OpenAPI annotations
```

### Available Override Files

| File | Affects Role |
|------|-------------|
| `.roles/product_manager.md` | Product Manager (`/sdd-feature`, `/sdd-stories`) |
| `.roles/system_architect.md` | System Architect (`/sdd-design`) |
| `.roles/tech_lead.md` | Tech Lead (`/sdd-tasks`, `/sdd-plan`, remediation) |
| `.roles/developer.md` | Developer (`/sdd-implement`) |
| `.roles/story_qa.md` | Story QA (`/sdd-implement`) |
| `.roles/task_qa.md` | Task QA (`/sdd-implement`) |

---

## Resumability

SDD is designed to be resumable. If a session is interrupted:

- **`/sdd-implement`** skips stories and tasks already marked `DONE`. Re-running the command continues from where it left off.
- **Workstreams** are auto-numbered (`WS_001`, `WS_002`, ...). Running `/sdd-design` again creates a new workstream rather than overwriting.
- **All state is in files.** There is no database or external state. You can inspect and manually edit any frontmatter if needed.

### Re-running Commands

```
# Safe to re-run — picks up where it left off
/sdd-implement checkout_resume

# Run a specific story that failed previously
/sdd-implement checkout_resume STORY_002

# Regenerate tasks (creates new files, doesn't overwrite DONE tasks)
/sdd-tasks checkout_resume
```

---

## Utility CLI

The `sdd-util` CLI provides deterministic state operations that the skills call via `"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh"`. You can also use it directly:

```bash
/path/to/plugins/sdd/scripts/sdd-util.sh --help
```

### Available Commands

| Command | Description |
|---------|-------------|
| `sdd-util init [--path DIR]` | Initialize project directories and INDEX.md |
| `sdd-util next-feature-number` | Print the next available FEAT number |
| `sdd-util next-story-number <dir>` | Print the next available STORY number |
| `sdd-util next-task-number <dir>` | Print the next available TASK number |
| `sdd-util find-feature <name>` | Find a feature directory by name/substring |
| `sdd-util find-workstream <name>` | Find the active workstream for a feature |
| `sdd-util create-workstream <slug>` | Create a new workstream directory |
| `sdd-util regenerate-index` | Regenerate INDEX.md |
| `sdd-util plan-json <name>` | Output development plan as JSON |

---

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=sdd

# Run a specific test file
poetry run pytest tests/test_state.py
```

### Linting

```bash
# Check for lint errors
poetry run ruff check src/ tests/

# Auto-fix lint errors
poetry run ruff check --fix src/ tests/
```

### Type Checking

```bash
poetry run mypy
```

---

## License

MIT
