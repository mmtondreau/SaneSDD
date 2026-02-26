#!/usr/bin/env bash
# Wrapper to run sdd-util from the plugin's Poetry environment.
# Navigate from plugins/sdd/scripts/ up to the repo root where pyproject.toml lives.
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
exec poetry -C "$REPO_ROOT" run sdd-util "$@"
