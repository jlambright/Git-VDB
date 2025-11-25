import pytest
from git_ai.domain.flight_recorder import FlightRecord

def test_flight_record_creation():
    """Tests basic creation of a FlightRecord."""
    record = FlightRecord(
        session_id="test_session",
        type="ACTION",
        intent="This is a test intent."
    )
    assert record.session_id == "test_session"
    assert record.type == "ACTION"
    assert record.intent == "This is a test intent."
    assert record.outcome == "PENDING"
    assert record.id is not None
    assert "ulid" not in record.id.lower() # Crockford's Base32 is uppercase
    assert len(record.id) == 26

def test_flight_record_id_uniqueness():
    """Tests that two records get unique ULIDs."""
    record1 = FlightRecord(session_id="test", type="THOUGHT", intent="i1")
    record2 = FlightRecord(session_id="test", type="THOUGHT", intent="i2")
    assert record1.id != record2.id

def test_to_ingestion_record():
    """Tests the ingestion record format."""
    record = FlightRecord(
        session_id="test_session",
        type="OBSERVATION",
        intent="Checking output.",
        git_hash="some_hash"
    )
    ingestion_data = record.to_ingestion_record()
    assert ingestion_data["id"] == record.id
    assert ingestion_data["session_id"] == "test_session"
    assert ingestion_data["type"] == "OBSERVATION"
    assert ingestion_data["git_hash"] == "some_hash"
    assert ingestion_data["outcome"] == "PENDING"
