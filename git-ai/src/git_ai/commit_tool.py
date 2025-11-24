import json
import jsonpatch
from typing import List, Dict, Any, Union

def structured_commit_tool(patch: Union[List[Dict[str, Any]], str], file_context: Dict[str, str]) -> Dict[str, Any]:
    """
    Apply a JSON Patch to the file context (simulating a commit).

    Args:
        patch (List[Dict] or str): The JSON Patch (RFC 6902) or string representation.
        file_context (Dict[str, str]): A dictionary where keys are file paths and values are file contents.
                                       This represents the current state of the files being modified.

    Returns:
        Dict[str, Any]: The result of the application, including modified files or errors.
    """
    if isinstance(patch, str):
        try:
            patch = json.loads(patch)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON string for patch"}

    try:
        # jsonpatch applies to a document.
        # We treat file_context as the document.
        # Paths in patch must start with / and match the keys in file_context.
        # e.g. path="/src/main.py" matches key "src/main.py" ??
        # No, JSON Pointer "/src/main.py" means key "src" then key "main.py".
        # But our keys are likely strings like "src/main.py".
        # If we use flat dictionary, we need to be careful with "/" in keys.
        # Standard JSON Pointer escapes "/" as "~1".
        # So "src/main.py" -> "/src~1main.py".

        # We should probably normalize the patch paths or the context structure.
        # For simplicity, let's assume the context is a nested dict or we adjust the patch.
        # Or better: The tool expects the patch to use correct JSON Pointers for the provided context structure.

        # Let's enforce that the input context is flat: {"path/to/file": "content"}
        # Then patch paths must be "/path~1to~1file".

        # AUTOMATIC HANDLING:
        # If the user provides path "/path/to/file", and our key is "path/to/file", jsonpatch won't match.
        # We can try to handle this, but strictly this tool applies the patch to the object provided.

        # Implementation:
        patch_obj = jsonpatch.JsonPatch(patch)
        result_doc = patch_obj.apply(file_context)
        return {"status": "success", "modified_context": result_doc}

    except jsonpatch.JsonPatchException as e:
        return {"error": f"Failed to apply patch: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
