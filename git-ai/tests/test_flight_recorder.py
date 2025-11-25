import pytest
from pydantic import ValidationError
from git_ai.domain.flight_recorder import (
    ThoughtRecord,
    ActionRecord,
    ObservationRecord,
    FeedbackRecord,
    FlightRecordState
)

def test_thought_record_creation():
    """Tests creation of a ThoughtRecord."""
    record = ThoughtRecord(session_id="test_session", intent="This is a test thought.")
    assert record.type == "THOUGHT"
    assert record.intent == "This is a test thought."
    assert record.session_id == "test_session"
    assert not hasattr(record, 'git_hash')

def test_action_record_creation():
    """Tests creation of an ActionRecord."""
    record = ActionRecord(
        session_id="test_session",
        intent="This is a test action.",
        git_hash="abcdef123"
    )
    assert record.type == "ACTION"
    assert record.git_hash == "abcdef123"
    assert record.intent == "This is a test action."

def test_action_record_missing_hash():
    """Tests that an ActionRecord requires a git_hash."""
    with pytest.raises(ValidationError):
        ActionRecord(session_id="test_session", intent="This should fail.")

def test_observation_record_creation():
    """Tests creation of an ObservationRecord."""
    record = ObservationRecord(session_id="test_session", intent="Observation details.")
    assert record.type == "OBSERVATION"
    assert not hasattr(record, 'git_hash')

def test_feedback_record_creation():
    """Tests creation of a FeedbackRecord."""
    record = FeedbackRecord(session_id="test_session", intent="User feedback provided.")
    assert record.type == "FEEDBACK"
    assert not hasattr(record, 'git_hash')

def test_record_id_uniqueness():
    """Tests that two records get unique ULIDs."""
    record1 = ThoughtRecord(session_id="test", intent="i1")
    record2 = ActionRecord(session_id="test", intent="i2", git_hash="hash123")
    assert record1.id != record2.id

def test_model_dump():
    """Tests that model_dump includes the type and other fields correctly."""
    record = ActionRecord(session_id="s1", intent="intent", git_hash="hash")
    dumped = record.model_dump()
    assert dumped['type'] == 'ACTION'
    assert dumped['git_hash'] == 'hash'
    assert dumped['intent'] == 'intent'
