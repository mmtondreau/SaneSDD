---
name: ssdd-status
description: Show the status of epics, stories, and tasks. Use to check project progress at any time.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "[name] [--type epic|story]"
---

# Show SaneSDD Status

This skill displays the current status of epics, stories, and tasks. It is a deterministic operation — no sub-agent is dispatched.

## Usage

```
/ssdd-status                        # Show all epics
/ssdd-status <name>                 # Show a specific epic or story (auto-detected)
/ssdd-status <name> --type epic     # Explicitly show an epic
/ssdd-status <name> --type story    # Explicitly show a story
```

## Step 1: Run Status Command

Run:
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/ssdd-util.sh" status $ARGUMENTS
```

If the command fails (e.g., epic or story not found), report the error to the user and STOP.

## Step 2: Display Results

Display the output from `ssdd-util status` directly to the user. The output is already formatted as a human-readable status report showing:

- Epic ID, title, and status
- Stories with task completion counts and approval status
- Task statuses (when viewing a specific story)

## User Input
$ARGUMENTS
