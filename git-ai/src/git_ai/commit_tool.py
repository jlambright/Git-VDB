import json
import jsonpatch
import os
from typing import List, Dict, Any, Union, Optional
from git_ai.utils import decode_pointer_to_file_path

def structured_commit_tool(
    patch: Union[List[Dict[str, Any]], str],
    file_context: Optional[Dict[str, str]] = None,
    root_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply a JSON Patch to either a file context dictionary OR directly to the filesystem.

    Args:
        patch (List[Dict] or str): The JSON Patch (RFC 6902).
        file_context (Dict[str, str], optional): In-memory context (legacy/testing mode).
        root_dir (str, optional): Root directory of the filesystem to apply changes to.
                                  If provided, 'file_context' is ignored (or treated as read-only context).

    Returns:
        Dict[str, Any]: Result status. If in-memory, returns modified context.
                        If filesystem, returns list of modified files.
    """
    if isinstance(patch, str):
        try:
            patch = json.loads(patch)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON string for patch"}

    if root_dir:
        return _apply_patch_to_filesystem(patch, root_dir)
    elif file_context is not None:
        return _apply_patch_in_memory(patch, file_context)
    else:
        return {"error": "Either file_context or root_dir must be provided."}

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
    Supports: add, remove, replace (replace file content).
    Limitations: Move/Copy/Test on file level not fully implemented for simplicity in this iteration,
                 or we map them to FS operations.
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

            # Security check: Ensure full_path is inside root_dir
            # (decode_pointer checks for .., but let's be double safe with resolve)
            try:
                # Resolve paths
                root_real = os.path.realpath(root_dir)
                full_real = os.path.realpath(full_path)
                # Note: full_real might not exist yet (for add), so we check parent or just generic prefix
                # If file doesn't exist, realpath might essentially be os.path.abspath if generic
                # Let's rely on common sense path checks
                if not os.path.abspath(full_path).startswith(os.path.abspath(root_dir)):
                     raise ValueError(f"Path traversal attempt: {rel_path}")
            except Exception as e:
                 raise ValueError(f"Path resolution error: {str(e)}")

            if operation == "replace" or operation == "add":
                value = op.get("value")
                if value is None:
                     raise ValueError(f"Missing 'value' for {operation}")

                # Ensure parent dir exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Write file
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(value)

                modified_files.append(rel_path)

            elif operation == "remove":
                if os.path.exists(full_path):
                    os.remove(full_path)
                    modified_files.append(rel_path + " (deleted)")

            else:
                # move, copy, test are harder on FS without reading first.
                # 'test' could check content.
                # For now, we support the core "Write Path" (replace/add).
                raise NotImplementedError(f"Filesystem operation '{operation}' not supported yet.")

        return {"status": "success", "modified_files": modified_files}

    except Exception as e:
        return {"error": f"Filesystem patch failed: {str(e)}"}
