---
name: ssdd-init
description: Initialize a new SaneSDD project with .ssdd/specs/, .ssdd/work/, and .ssdd/design/ directories and INDEX.md. For existing projects, also generates design docs from the codebase.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "[path]"
---

# Initialize SaneSDD Project

## Step 1: Create Directory Structure

Run the init command to create the SaneSDD directory structure:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" init $ARGUMENTS
```

Report which directories were created and which already existed.

## Step 2: Ask If This Is an Existing Project

Ask the user: **"Is this an existing project with code already in it, or a brand-new project?"**

- If the user says this is a **new/fresh project**, skip to the Final Message.
- If the user says this is an **existing project**, proceed to Step 3.

## Step 3: Generate INDEX.md First

For existing projects, regenerate INDEX.md immediately so it captures the current state of any existing files:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" regenerate-index
```

## Step 4: Ask for Existing Documentation

Ask the user: **"Do you have any existing documentation (architecture docs, READMEs, wiki pages, design docs, API specs, etc.) that I should use as input for generating the design? If so, please share the file paths or paste the content."**

- If the user provides file paths, read those files.
- If the user pastes content, use it directly.
- If the user says no or has none, proceed using only the codebase.

## Step 5: Generate Design Documents

You are now acting as the **System Architect**. Read the codebase (and any user-provided documentation) and generate design documentation.

### Templates

Read these templates and use them as structural guides — they are the same templates that `/ssdd-design` uses:
- `${CLAUDE_PLUGIN_ROOT}/skills/ssdd-design/reference/design-template.md` — for .ssdd/design/design.md
- `${CLAUDE_PLUGIN_ROOT}/skills/ssdd-design/reference/domain-template.md` — for each domain.md within domain directories
- `${CLAUDE_PLUGIN_ROOT}/skills/ssdd-design/reference/component-design-template.md` — for each COMP_*.md within domain directories

### Process

1. **Read INDEX.md** for an overview of existing project structure.

2. **Survey the codebase.** Read key files: entry points, configuration files (package.json, pyproject.toml, Cargo.toml, go.mod, etc.), directory structure, and representative source files. Understand the project's language, framework, and architecture.

3. **Incorporate existing documentation.** If the user provided docs in Step 4, use them as primary context. Cross-reference against the actual code to verify accuracy. Prefer information from the code when docs and code disagree.

4. **Identify domains and components.** Look for natural bounded contexts: modules, packages, services, or layers (e.g., API, data access, business logic, UI). Group related components into domains. Each distinct area of responsibility becomes a component within a domain.

5. **Generate `.ssdd/design/design.md`** using the design template as the structural guide. Include a Domain Index and Component Index.

6. **Generate all `domain.md` files first (breadth-first).** Before writing any component docs, create every domain directory and its `domain.md`. For each domain identified in step 4:
   - Run `ssdd-util next-domain-number` to get the next available number.
   - Create the directory `.ssdd/design/DOMAIN_NNN_<name>/`.
   - Generate `.ssdd/design/DOMAIN_NNN_<name>/domain.md` using the domain template as the structural guide.

   Complete all domain.md files before proceeding. This establishes the full generalized picture of bounded contexts across the system.

7. **Generate component docs within each domain.** Now that all domains are defined, go back through each domain and generate `.ssdd/design/DOMAIN_NNN_<name>/COMP_<name>.md` for each component, using the component design template as the structural guide.

Base all content on what you observe in the actual code and any provided documentation — do not speculate or add aspirational content. Document what exists.

8. **Regenerate INDEX.md** to capture the newly created design files:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" regenerate-index
```

## Final Message

After completing all steps, tell the user:

> **Next step:** Run `/ssdd-feature` to define your first feature. Run `/ssdd-help` for a full workflow overview.

If design documents were generated for an existing project, also display a **Files to review** section listing every file that was created or modified, grouped by type. Use this format:

> **Files to review:**
>
> System architecture:
> - `.ssdd/design/design.md`
>
> Domains:
> - `.ssdd/design/DOMAIN_001_<name>/domain.md`
> - `.ssdd/design/DOMAIN_002_<name>/domain.md`
> - _(list all)_
>
> Components:
> - `.ssdd/design/DOMAIN_001_<name>/COMP_<name>.md`
> - _(list all)_

List the actual file paths that were generated — do not use glob patterns. Then tell the user:

> Review these files for accuracy before proceeding. Domains define your system's bounded contexts; components detail the internal structure. Use `/ssdd-feature` to define your next feature.
