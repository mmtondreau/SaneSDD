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

## Step 2: Ask If This Is an Existing Project

Ask the user: **"Is this an existing project with code already in it, or a brand-new project?"**

- If the user says this is a **new/fresh project**, skip to the Final Message.
- If the user says this is an **existing project**, proceed to Step 3.

## Step 3: Generate INDEX.md First

For existing projects, regenerate INDEX.md immediately so it captures the current state of any existing files:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

## Step 4: Ask for Existing Documentation

Ask the user: **"Do you have any existing documentation (architecture docs, READMEs, wiki pages, design docs, API specs, etc.) that I should use as input for generating the design? If so, please share the file paths or paste the content."**

- If the user provides file paths, read those files.
- If the user pastes content, use it directly.
- If the user says no or has none, proceed using only the codebase.

## Step 5: Generate Design Documents

You are now acting as the **System Architect**. Read the codebase (and any user-provided documentation) and generate design documentation.

### Templates

Read these templates and use them as structural guides — they are the same templates that `/sdd-design` uses:
- `${CLAUDE_PLUGIN_ROOT}/skills/sdd-design/reference/design-template.md` — for design/design.md
- `${CLAUDE_PLUGIN_ROOT}/skills/sdd-design/reference/component-design-template.md` — for each COMP_*.md within domain directories

### Process

1. **Read INDEX.md** for an overview of existing project structure.

2. **Survey the codebase.** Read key files: entry points, configuration files (package.json, pyproject.toml, Cargo.toml, go.mod, etc.), directory structure, and representative source files. Understand the project's language, framework, and architecture.

3. **Incorporate existing documentation.** If the user provided docs in Step 4, use them as primary context. Cross-reference against the actual code to verify accuracy. Prefer information from the code when docs and code disagree.

4. **Identify domains and components.** Look for natural bounded contexts: modules, packages, services, or layers (e.g., API, data access, business logic, UI). Group related components into domains. Each distinct area of responsibility becomes a component within a domain.

5. **Generate `design/design.md`** using the design template as the structural guide. Include a Domain Index and Component Index.

6. **Generate domain directories and component docs.** For each domain, create `design/DOMAIN_NNN_<name>/` and generate `design/DOMAIN_NNN_<name>/COMP_<name>.md` for each component, using the component design template as the structural guide. Use `sdd-util next-domain-number` to determine the next available domain number.

Base all content on what you observe in the actual code and any provided documentation — do not speculate or add aspirational content. Document what exists.

7. **Regenerate INDEX.md** to capture the newly created design files:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" regenerate-index
```

## Final Message

After completing all steps, tell the user:

> **Next step:** Run `/sdd-feature` to define your first feature. Run `/sdd-help` for a full workflow overview.

If design documents were generated for an existing project, also tell the user:

> Design documents have been generated from your existing codebase. Review `design/design.md` and `design/DOMAIN_*/COMP_*.md` to verify accuracy, then use `/sdd-feature` to define your next feature.
