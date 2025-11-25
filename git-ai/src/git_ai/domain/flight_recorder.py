from typing import Union, List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict
import ulid
import datetime

# 1. Base Class (The Core OOI Structure)
class FlightRecord(BaseModel):
    """
    The base Object of Importance for a single recorded event.
    """
    model_config = ConfigDict(frozen=True)

    # Core Identity & Timestamping
    id: str = Field(default_factory=lambda: str(ulid.new()), alias="id")
    session_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    # The "Why" - Natural language description of the goal.
    intent: str = Field(json_schema_extra={"embedding_target": True})

    # The "Evidence" - Verification layer providing context for the action.
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # The "Train" - RLHF labels.
    outcome: Literal["PENDING", "ACCEPTED", "REJECTED"] = "PENDING"

# 2. State Subclasses (The Discriminated Union Members)

class ThoughtRecord(FlightRecord):
    """A record of the agent's internal reasoning."""
    type: Literal['THOUGHT'] = 'THOUGHT'

class ActionRecord(FlightRecord):
    """A record of a specific action taken by the agent (e.g., a commit)."""
    type: Literal['ACTION'] = 'ACTION'
    git_hash: str  # The git_hash is REQUIRED for an action.

class ObservationRecord(FlightRecord):
    """A record of an observation from the environment (e.g., a tool's output)."""
    type: Literal['OBSERVATION'] = 'OBSERVATION'

class FeedbackRecord(FlightRecord):
    """A record of feedback from a human or supervisor."""
    type: Literal['FEEDBACK'] = 'FEEDBACK'


# 3. The OOI Union (The Complete Type Definition)
FlightRecordState = Union[ThoughtRecord, ActionRecord, ObservationRecord, FeedbackRecord]
