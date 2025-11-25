import json
import jsonpatch
import os
from typing import List, Dict, Any, Union, Optional
from git_ai.utils import decode_pointer_to_file_path
from git_ai.domain.git_repo import GitRepository

def structured_commit_tool(
    patch: Union[List[Dict[str, Any]], str],
    vdb_id: str,
    commit_message: str,
    root_dir: Optional[str] = None,
    file_context: Optional[Dict[str, str]] = None,
    amend: bool = False # Kept for signature compatibility, but will be enforced as False
) -> Dict[str, Any]:
    """
    Apply a JSON Patch and commit it with a VDB ID footer.
    Note: `amend` is disallowed by the GIT-VDB ARCHITECTURAL DIRECTIVE.

    Args:
        patch (List[Dict] or str): The JSON Patch (RFC 6902).
        vdb_id (str): The ULID for the Flight Record, required for the commit footer.
        commit_message (str): The commit message.
        root_dir (str, optional): Root directory of the filesystem to apply changes to.
        file_context (Dict[str, str], optional): In-memory context (legacy/testing mode).
        amend (bool): Disallowed. Will raise an error if True.

    Returns:
        Dict[str, Any]: Result status, modified files, and 'commit_hash'.
    """
    if amend:
        return {"error": "Amending commits is disallowed by the GIT-VDB directive."}

    if isinstance(patch, str):
        try:
            patch = json.loads(patch)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON string for patch"}

    # Apply changes
    result = {}
    # This tool is primarily for filesystem operations and commits.
    # In-memory mode is a legacy feature and does not support commits.
    if not root_dir:
        if file_context is not None:
            return _apply_patch_in_memory(patch, file_context)
        return {"error": "root_dir must be provided for git operations."}

    result = {}
    patch_result = _apply_patch_to_filesystem(patch, root_dir)
    if "error" in patch_result:
        return patch_result
    result.update(patch_result)

    # Commit to Git
    try:
        repo = GitRepository(root_dir)

        # Format commit message with VDB ID footer
        full_commit_message = f"{commit_message}\n\nGit-VDB-ID: {vdb_id}"

        commit_hash = repo.commit_changes(full_commit_message)

        result["commit_hash"] = commit_hash
        result["commit_status"] = "success"
    except Exception as e:
        result["commit_status"] = f"failed: {str(e)}"

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

                # Ensure the directory exists before writing the file
                dir_name = os.path.dirname(full_path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)

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
