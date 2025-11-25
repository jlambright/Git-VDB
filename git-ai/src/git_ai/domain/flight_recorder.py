from typing import Union, List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict
import ulid
import datetime

class FlightRecord(BaseModel):
    """
    The atomic unit of the Vector Database index, representing a single
    thought, action, or observation in the agent's execution loop.
    """
    model_config = ConfigDict(frozen=True)

    # Core Identity & Timestamping
    id: str = Field(default_factory=lambda: str(ulid.new()), alias="id")
    session_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Type Discriminator
    type: Literal["THOUGHT", "ACTION", "OBSERVATION", "FEEDBACK"]

    # The "Why" - Natural language description of the goal.
    # This is the primary target for semantic search.
    intent: str = Field(embedding_target=True)

    # The "Evidence" - Verification layer providing context for the action.
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # The "State" - Linkage to the Git repository state.
    # This is nullable because THOUGHT, OBSERVATION, or FEEDBACK records
    # may not correspond to a specific code change.
    git_hash: Optional[str] = None

    # The "Train" - RLHF (Reinforcement Learning from Human Feedback) labels.
    # Starts as PENDING and is updated upon review.
    outcome: Literal["PENDING", "ACCEPTED", "REJECTED"] = "PENDING"

    def to_ingestion_record(self) -> Dict[str, Any]:
        """
        Prepares the record for ingestion into the Vector DB.
        This is where we would flatten the structure or select specific
        fields for different parts of the VDB (e.g., payload vs. vector).
        """
        record = self.model_dump(by_alias=True)
        # In a real implementation, you might transform the 'intent' field
        # into a vector here before sending it to the VDB.
        return record
