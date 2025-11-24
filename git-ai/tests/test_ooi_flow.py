import pytest
from git_ai.domain.ooi import TaskRequested, ContextRetrieved, PatchGenerated, ChangeCommitted
from git_ai.domain.factory import CodeChangeTaskFactory

def test_ooi_flow():
    # 1. Create Initial Task
    query = "Fix the bug in the login module"
    task = CodeChangeTaskFactory.create_initial(query)

    assert isinstance(task, TaskRequested)
    assert task.query == query
    assert task.task_id is not None

    # 2. Transition to Context Retrieved
    search_results = [{"score": 0.9, "payload": {"text": "def login(): ..."}}]
    task_context = CodeChangeTaskFactory.transition_to_context_retrieved(task, search_results)

    assert isinstance(task_context, ContextRetrieved)
    assert task_context.task_id == task.task_id
    assert task_context.search_results == search_results
    assert task_context.query == query

    # 3. Transition to Patch Generated
    patch = [{"op": "replace", "path": "/login.py", "value": "new_code"}]
    task_patch = CodeChangeTaskFactory.transition_to_patch_generated(task_context, patch)

    assert isinstance(task_patch, PatchGenerated)
    assert task_patch.patch == patch

    # 4. Transition to Change Committed
    commit_hash = "abc1234"
    task_committed = CodeChangeTaskFactory.transition_to_change_committed(task_patch, commit_hash)

    assert isinstance(task_committed, ChangeCommitted)
    assert task_committed.commit_hash == commit_hash

def test_ooi_protection_checks():
    query = "Test query"
    task = CodeChangeTaskFactory.create_initial(query)

    # Try illegal transition (skip context)
    patch = [{"op": "replace", "path": "/test", "value": "val"}]
    with pytest.raises(TypeError, match="Transition only allowed from ContextRetrieved"):
        CodeChangeTaskFactory.transition_to_patch_generated(task, patch) # type: ignore

    # Try invalid data (empty search results - though empty list might be valid, Factory checks strict None? Code says "if search_results is None")
    with pytest.raises(ValueError):
        CodeChangeTaskFactory.transition_to_context_retrieved(task, None) # type: ignore

    # Try invalid patch format
    search_results = []
    task_context = CodeChangeTaskFactory.transition_to_context_retrieved(task, search_results)
    invalid_patch = [{"op": "invalid"}] # Missing path
    with pytest.raises(ValueError, match="Invalid JSON Patch"):
        CodeChangeTaskFactory.transition_to_patch_generated(task_context, invalid_patch)
