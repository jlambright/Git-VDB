import json
import jsonpatch
from pydantic import BaseModel, ValidationError, ConfigDict, Field
from typing import List, Dict, Any, Union

class JSONPatchOp(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    op: str
    path: str
    value: Any = None
    from_: str = Field(default=None, alias='from')

class CommitPayload(BaseModel):
    patch: List[JSONPatchOp]
    commit_message: str

def validate_and_format_patch(raw_patch: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Validates that the input is a valid JSON Patch and strictly conforms to schema.
    Returns the list of operations if valid.
    """
    if isinstance(raw_patch, str):
        try:
            raw_patch = json.loads(raw_patch)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string.")

    if not isinstance(raw_patch, list):
         raise ValueError("Patch must be a list of operations.")

    # Validate using Pydantic
    try:
        validated_patch = [JSONPatchOp(**op).model_dump(by_alias=True, exclude_none=True) for op in raw_patch]
        return validated_patch
    except ValidationError as e:
        raise ValueError(f"Patch schema validation failed: {e}")

def generate_patch_prompt(task_description: str, context: str) -> str:
    """
    Helper to generate the prompt (using the strategy defined in M4).
    """
    # Load the template (in a real app, read from the file)
    template = """
**Objective:**
Generate a valid JSON Patch (RFC 6902) to apply the necessary code changes.

**Input:**
- User Task: "{user_task}"
- Retrieved Context:
{context_json}

**Instructions:**
1. Analyze the retrieved context.
2. Construct a JSON Patch that modifies the file(s) correctly.
3. The context provided is a JSON object where keys are file paths (e.g. "src/main.py") and values are content.
4. **Crucial**: To target a key like "src/main.py", your path MUST be escaped as "/src~1main.py".
   - "/" is escaped as "~1".
   - "~" is escaped as "~0".
5. Output ONLY the JSON Patch list.

**Example:**
Task: "Change print hello to print world in main.py"
Context: {"main.py": "print('hello')"}
Output: [{"op": "replace", "path": "/main.py", "value": "print('world')"}]
"""
    return template.format(user_task=task_description, context_json=context)
