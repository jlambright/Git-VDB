import os
import sys
from fastmcp import FastMCP
from typing import List, Dict, Any, Optional

# Import our domain tools
from git_ai.tools import semantic_search_tool
from git_ai.commit_tool import structured_commit_tool
from git_ai.revert_tool import revert_change_tool

# Initialize FastMCP Server
mcp = FastMCP("git-ai")

# Configuration
# Default to current directory if not set
DEFAULT_REPO_PATH = os.getcwd()

@mcp.tool()
def search_code(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a semantic search to retrieve relevant code context from the index.

    Args:
        query (str): The search query describing what code you are looking for.
        limit (int): Max results to return.
    """
    # Environment variable INDEXER_URL is used by semantic_search_tool internally
    return semantic_search_tool(query, limit)

@mcp.tool()
def apply_commit(patch: str, commit_message: str, amend: bool = False) -> Dict[str, Any]:
    """
    Apply a structured JSON Patch to the codebase and commit it via Git.

    Args:
        patch (str): A valid JSON Patch string (RFC 6902).
        commit_message (str): The git commit message.
        amend (bool): If True, amend the previous commit instead of creating a new one.
    """
    repo_path = os.environ.get("GIT_REPO_PATH", DEFAULT_REPO_PATH)

    # We use our structured_commit_tool which handles filesystem application and git commit
    return structured_commit_tool(
        patch=patch,
        root_dir=repo_path,
        commit_message=commit_message,
        amend=amend
    )

@mcp.tool()
def revert_last_commit(commit_hash: str) -> Dict[str, Any]:
    """
    Revert a specific git commit by creating a new inverse commit.

    Args:
        commit_hash (str): The hash of the commit to revert.
    """
    repo_path = os.environ.get("GIT_REPO_PATH", DEFAULT_REPO_PATH)
    return revert_change_tool(commit_hash, repo_path)

if __name__ == "__main__":
    mcp.run()
