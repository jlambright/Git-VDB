import pytest
from git_ai.domain.ooi import TaskRequested, ContextRetrieved
from git_ai.domain.factory import CodeChangeTaskFactory

def test_state_transition_vs_simple_update():
    # 1. Setup: Initial State
    query = "Fix bug"
    task = CodeChangeTaskFactory.create_initial(query)
    original_id = task.task_id
    assert isinstance(task, TaskRequested)
    assert task.query == "Fix bug"

    # CASE A: Simple Update (Intra-state)
    # Scenario: User corrects the query before retrieval.
    # We stay in TaskRequested.
    updated_task = task.copy_with(query="Fix bug in login")

    assert isinstance(updated_task, TaskRequested) # Type is preserved
    assert updated_task.query == "Fix bug in login"
    assert updated_task.task_id == original_id     # ID preserved
    assert updated_task is not task                # Immutability: New instance

    # Verify Validation works in Simple Update
    # Assuming there's some validation (e.g. strict types).
    # Pydantic validates types on init.
    with pytest.raises(Exception): # ValidationError
        task.copy_with(query=123) # Invalid type

    # CASE B: State Transition (Inter-state)
    # Scenario: Context is retrieved.
    # We move to ContextRetrieved.
    # We use the Factory (which uses copy_to internally)
    search_results = [{"payload": {"text": "code"}}]

    # Note: We use the *updated_task* from Case A to proceed
    next_task = CodeChangeTaskFactory.transition_to_context_retrieved(updated_task, search_results)

    assert isinstance(next_task, ContextRetrieved) # Type changed!
    assert next_task.query == "Fix bug in login"   # Data carried over
    assert next_task.task_id == original_id        # ID preserved
    assert next_task.search_results == search_results

def test_copy_with_manual_usage():
    """Verify copy_with works directly on the object."""
    task = CodeChangeTaskFactory.create_initial("Initial")

    # Update arbitrary field valid for this class
    # (Note: 'created_at' is in base)
    new_time = task.created_at + 100
    task_v2 = task.copy_with(created_at=new_time)

    assert task_v2.created_at == new_time
    assert task_v2.query == "Initial"
