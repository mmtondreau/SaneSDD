---
name: sdd-init
description: Initialize a new SDD project with specs/, work/, and design/ directories and INDEX.md. For existing projects, also generates design docs from the codebase.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "[path]"
---

# Initialize SDD Project

## Step 1: Create Directory Structure

Run the init command to create the SDD directory structure:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" init $ARGUMENTS
```

Report which directories were created and which already existed.

## Step 2: Detect Existing Project

After initialization, check whether this is an existing project with code by looking for source files (e.g., `*.py`, `*.ts`, `*.js`, `*.java`, `*.go`, `*.rs`, `*.rb`, `*.cs`, `*.cpp`, `*.c`, `*.swift`, `*.kt`). Glob for common source file patterns in the project root, excluding `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `.git/`, and other typical ignored directories.

If **no source files are found**, this is a fresh project. Skip to the final message.

If **source files are found**, this is an existing project. Proceed to Step 3.

## Step 3: Generate Design Documents for Existing Projects

You are now acting as the **System Architect**. Read the codebase and generate design documentation.

### Templates
Read these templates and use them as structural guides:
- `${CLAUDE_PLUGIN_ROOT}/skills/sdd-design/reference/high-level-design-template.md` — structural reference (use the design.md Structure below for the global doc)
- `${CLAUDE_PLUGIN_ROOT}/skills/sdd-design/reference/component-design-template.md` — for each COMP_*.md

### Process

1. **Survey the codebase.** Read key files: entry points, configuration files (package.json, pyproject.toml, Cargo.toml, go.mod, etc.), directory structure, and representative source files. Understand the project's language, framework, and architecture.

2. **Identify components.** Look for natural boundaries: modules, packages, services, major classes, or layers (e.g., API, data access, business logic, UI). Each distinct area of responsibility becomes a component.

3. **Generate `design/design.md`.** Write the global architecture document with this structure:

```markdown
# System Architecture

## Overview
[System-wide architectural summary based on the existing codebase.]

## Component Map
[How components relate to each other. ASCII diagram or prose description.]

## System-Level Data Flow
[How data flows across the full system.]

## Cross-Cutting Concerns
[Authentication, logging, error handling, monitoring — anything that spans components.]

## Component Index
| Component | Design Doc | Purpose | Status |
|-----------|-----------|---------|--------|
| <Name> | `design/COMP_<name>.md` | <1-line purpose> | Existing |
```

4. **Generate `design/COMP_<name>.md`** for each identified component. Each COMP doc must use YAML frontmatter and include these sections:

```yaml
---
component: "<ComponentName>"
depends_on: []
stories: []
updated: "<today's date YYYY-MM-DD>"
---
```

Sections: Purpose, Public Interface (functions/methods, events/signals), Internal Structure, Data Models, Error Handling, Dependencies, Testing Strategy.

Base all content on what you observe in the actual code — do not speculate or add aspirational content. Document what exists.

5. **Regenerate INDEX.md:**
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

## Final Message

After completing all steps, tell the user:

> **Next step:** Run `/sdd-feature` to define your first feature. Run `/sdd-help` for a full workflow overview.

If design documents were generated for an existing project, also tell the user:

> Design documents have been generated from your existing codebase. Review `design/design.md` and `design/COMP_*.md` to verify accuracy, then use `/sdd-feature` to define your next feature.
