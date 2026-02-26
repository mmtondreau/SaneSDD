---
name: sdd-init
description: Initialize a new SDD project with specs/, work/, and design/ directories and INDEX.md.
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash
argument-hint: "[path]"
---

# Initialize SDD Project

Run the init command to create the SDD directory structure:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/sdd-util.sh" init $ARGUMENTS
```

Report which directories were created and which already existed.
