#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install OpLab MCP server dependencies
pip3 install mcp httpx --ignore-installed --break-system-packages -q 2>&1 | tail -3

# Resolve token: prefer env var, fall back to embedded value
OPLAB_TOKEN="${OPLAB_ACCESS_TOKEN:-AnJFCmWtZiSCL9Up1F2slrKpbhg/SIUuWj7ohDwxQ4Uvk1/2CY9bUI8KaPofVzT0--X8vvuqmk7JeKDuYquob/lA==--MzVlYTVhYzY0ODkyM2Y0Y2ZlOTkwMjcyNTM2ZWFjNDg=}"

# Write MCP server config into ~/.claude/settings.json
# Reads existing file and merges, preserving all other settings
python3 - <<PYEOF
import json, os, sys

settings_path = os.path.expanduser("~/.claude/settings.json")

try:
    with open(settings_path) as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    settings = {}

settings.setdefault("mcpServers", {})["oplab"] = {
    "command": "python3",
    "args": ["${CLAUDE_PROJECT_DIR}/oplab_server.py"],
    "env": {
        "OPLAB_ACCESS_TOKEN": "${OPLAB_TOKEN}"
    }
}

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w") as f:
    json.dump(settings, f, indent=4)

print("OpLab MCP server configured in ~/.claude/settings.json")
PYEOF
