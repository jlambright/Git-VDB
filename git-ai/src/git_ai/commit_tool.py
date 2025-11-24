import json
import jsonpatch
import os
from typing import List, Dict, Any, Union, Optional
from git_ai.utils import decode_pointer_to_file_path
from git_ai.domain.git_repo import GitRepository

def structured_commit_tool(
    patch: Union[List[Dict[str, Any]], str],
    file_context: Optional[Dict[str, str]] = None,
    root_dir: Optional[str] = None,
    commit_message: Optional[str] = None,
    amend: bool = False
) -> Dict[str, Any]:
    """
    Apply a JSON Patch to either a file context dictionary OR directly to the filesystem.
    If root_dir is provided AND it is a git repo, it can optionally commit the changes.

    Args:
        patch (List[Dict] or str): The JSON Patch (RFC 6902).
        file_context (Dict[str, str], optional): In-memory context (legacy/testing mode).
        root_dir (str, optional): Root directory of the filesystem to apply changes to.
        commit_message (str, optional): If provided, and root_dir is a git repo, changes will be committed.
        amend (bool): If True, amends the previous commit instead of creating a new one.

    Returns:
        Dict[str, Any]: Result status, modified files, and optionally 'commit_hash'.
    """
    if isinstance(patch, str):
        try:
            patch = json.loads(patch)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON string for patch"}

    # Apply changes
    result = {}
    if root_dir:
        patch_result = _apply_patch_to_filesystem(patch, root_dir)
        if "error" in patch_result:
            return patch_result
        result.update(patch_result)

        # Optional: Commit to Git
        if commit_message:
            try:
                repo = GitRepository(root_dir)

                # Commit or Amend
                if amend:
                    commit_hash = repo.amend_changes(commit_message)
                else:
                    commit_hash = repo.commit_changes(commit_message)

                result["commit_hash"] = commit_hash
                result["commit_status"] = "success"
                result["amended"] = amend
            except Exception as e:
                result["commit_status"] = f"failed: {str(e)}"

    elif file_context is not None:
        if amend:
            return {"error": "Amend not supported in in-memory mode."}
        return _apply_patch_in_memory(patch, file_context)
    else:
        return {"error": "Either file_context or root_dir must be provided."}

    return result

def _apply_patch_in_memory(patch, file_context):
    try:
        patch_obj = jsonpatch.JsonPatch(patch)
        result_doc = patch_obj.apply(file_context)
        return {"status": "success", "modified_context": result_doc}
    except jsonpatch.JsonPatchException as e:
        return {"error": f"Failed to apply patch: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def _apply_patch_to_filesystem(patch: List[Dict[str, Any]], root_dir: str) -> Dict[str, Any]:
    """
    Applies operations directly to files in root_dir.
    """
    modified_files = []

    try:
        for op in patch:
            operation = op.get("op")
            path_pointer = op.get("path")

            if not operation or not path_pointer:
                raise ValueError("Operation missing 'op' or 'path'")

            # Decode pointer to relative file path
            try:
                rel_path = decode_pointer_to_file_path(path_pointer)
            except ValueError as e:
                raise ValueError(f"Invalid path in patch: {str(e)}")

            full_path = os.path.join(root_dir, rel_path)

            # Security check
            try:
                if not os.path.abspath(full_path).startswith(os.path.abspath(root_dir)):
                     raise ValueError(f"Path traversal attempt: {rel_path}")
            except Exception as e:
                 raise ValueError(f"Path resolution error: {str(e)}")

            if operation == "replace" or operation == "add":
                value = op.get("value")
                if value is None:
                     raise ValueError(f"Missing 'value' for {operation}")

                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(value)
                modified_files.append(rel_path)

            elif operation == "remove":
                if os.path.exists(full_path):
                    os.remove(full_path)
                    modified_files.append(rel_path + " (deleted)")

            else:
                raise NotImplementedError(f"Filesystem operation '{operation}' not supported yet.")

        return {"status": "success", "modified_files": modified_files}

    except Exception as e:
        return {"error": f"Filesystem patch failed: {str(e)}"}
