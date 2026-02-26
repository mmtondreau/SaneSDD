#!/usr/bin/env bash
# Wrapper to run sdd-util from the plugin's Poetry environment.
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec poetry -C "$PLUGIN_ROOT" run sdd-util "$@"
