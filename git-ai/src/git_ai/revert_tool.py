from typing import Dict, Any
from git_ai.domain.git_repo import GitRepository

def revert_change_tool(commit_hash: str, root_dir: str) -> Dict[str, Any]:
    """
    Reverts a specific git commit.

    Args:
        commit_hash (str): The hash of the commit to revert.
        root_dir (str): The repository root directory.

    Returns:
        Dict[str, Any]: Status and new commit hash.
    """
    try:
        repo = GitRepository(root_dir)
        new_commit_hash = repo.revert_commit(commit_hash)
        return {
            "status": "success",
            "message": f"Reverted commit {commit_hash}",
            "revert_commit_hash": new_commit_hash
        }
    except Exception as e:
        return {"error": f"Failed to revert commit: {str(e)}"}
