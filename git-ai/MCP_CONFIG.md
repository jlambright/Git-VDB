# MCP Configuration Guide

This `git-ai` tool is designed to function as a Model Context Protocol (MCP) server.

## Connection Strategy
We prioritize **Local Repository Binding**. The MCP server should run in an environment where it has filesystem access to the git repository you wish to manage. This leverages your existing local git authentication (SSH keys, Credential Helpers).

## Configuration Variables

The following environment variables must be set when running the MCP server:

| Variable | Description | Default |
|----------|-------------|---------|
| `GIT_REPO_PATH` | Absolute path to the local git repository root. | `.` (Current Working Dir) |
| `INDEXER_URL` | URL of the running Indexer Service (Qdrant wrapper). | `http://localhost:8000` |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, ERROR). | `INFO` |

## Authentication
- **Local:** No extra auth needed if your local user can push/pull to the repo.
- **Remote (Containerized):** If running in a container, map your SSH socket or provide `GIT_USERNAME` / `GIT_PASSWORD` (PAT) environment variables if `GitPython` needs to clone/push.

## Example Usage (Claude Desktop)

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "git-ai": {
      "command": "python3",
      "args": ["-m", "git_ai.mcp_server"],
      "env": {
        "GIT_REPO_PATH": "/Users/me/projects/my-repo",
        "INDEXER_URL": "http://localhost:8000"
      }
    }
  }
}
```
