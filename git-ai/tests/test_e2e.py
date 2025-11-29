import pytest
import json
from git_ai.domain.ooi import TaskRequested, ContextRetrieved, PatchGenerated, ChangeCommitted
from git_ai.domain.factory import CodeChangeTaskFactory
from git_ai.utils import validate_and_format_patch
from git_ai.commit_tool import structured_commit_tool

def test_e2e_flow():
    # 1. User Request
    query = "Fix the typo in README.md"
    task = CodeChangeTaskFactory.create_initial(query)
    assert isinstance(task, TaskRequested)

    # 2. Retrieve Context (Simulated)
    # Assume we searched and found README.md
    initial_file_content = {"README.md": "Hello Wolrd"} # Typo
    search_results = [{"score": 1.0, "payload": {"text": "Hello Wolrd", "filename": "README.md"}}]

    task = CodeChangeTaskFactory.transition_to_context_retrieved(task, search_results)
    assert isinstance(task, ContextRetrieved)

    # 3. Generate Patch (Simulated LLM Output)
    # LLM should produce this patch to fix "Wolrd" -> "World"
    # Note: JSON Pointer escaping for "README.md" is not needed if it doesn't contain "/" or "~".
    # But if it was "src/README.md", it would be "/src~1README.md".
    raw_patch = [
        {"op": "replace", "path": "/README.md", "value": "Hello World"}
    ]

    # Enforce/Validate Patch
    valid_patch = validate_and_format_patch(raw_patch)

    task = CodeChangeTaskFactory.transition_to_patch_generated(task, valid_patch)
    assert isinstance(task, PatchGenerated)

    # 4. Commit/Apply Change
    # We apply the patch to the "file context"
    result = structured_commit_tool(task.patch, initial_file_content)

    assert "error" not in result
    modified_context = result["modified_context"]
    assert modified_context["README.md"] == "Hello World"

    # Transition to Committed (Simulated hash)
    task = CodeChangeTaskFactory.transition_to_change_committed(task, "commit_hash_123")
    assert isinstance(task, ChangeCommitted)
    assert task.commit_hash == "commit_hash_123"

def test_json_pointer_escaping():
    # Test complex path
    initial_context = {"src/app/main.py": "print('old')"}
    # Path "src/app/main.py" -> "/src~1app~1main.py"
    raw_patch = [
        {"op": "replace", "path": "/src~1app~1main.py", "value": "print('new')"}
    ]

    valid_patch = validate_and_format_patch(raw_patch)
    result = structured_commit_tool(valid_patch, initial_context)

    assert result["modified_context"]["src/app/main.py"] == "print('new')"
