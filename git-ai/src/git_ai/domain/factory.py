import uuid
import time
from typing import List, Dict, Any, Union
from git_ai.domain.ooi import (
    CodeChangeTaskState,
    TaskRequested,
    ContextRetrieved,
    PatchGenerated,
    ChangeCommitted
)

class CodeChangeTaskFactory:
    """
    OOI Factory Class: The exclusive point of construction and transition for CodeChangeTask.
    """
    @classmethod
    def create_initial(cls, query: str) -> 'TaskRequested':
        """Factory Method for OOI creation."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        return TaskRequested(
            task_id=str(uuid.uuid4()),
            created_at=time.time(),
            query=query
        )

    @classmethod
    def transition_to_context_retrieved(
        cls,
        current_ooi: 'TaskRequested',
        search_results: List[Dict[str, Any]]
    ) -> 'ContextRetrieved':
        """Transition Factory Method: TaskRequested -> ContextRetrieved."""
        # OOI PROTECTION: State check is MANDATORY
        if not isinstance(current_ooi, TaskRequested):
            raise TypeError("Transition only allowed from TaskRequested state.")

        # OOI PROTECTION: Transition validation logic
        if search_results is None:
            raise ValueError("Search results cannot be None.")

        # Use copy_to for transition
        return current_ooi.copy_to(
            ContextRetrieved,
            search_results=search_results
        )

    @classmethod
    def transition_to_patch_generated(
        cls,
        current_ooi: 'ContextRetrieved',
        patch: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> 'PatchGenerated':
        """Transition Factory Method: ContextRetrieved -> PatchGenerated."""
        # OOI PROTECTION: State check is MANDATORY
        if not isinstance(current_ooi, ContextRetrieved):
            raise TypeError("Transition only allowed from ContextRetrieved state.")

        # OOI PROTECTION: Transition validation logic
        if not patch:
            raise ValueError("Patch cannot be empty.")

        # Basic JSON Patch validation
        if isinstance(patch, list):
             for op in patch:
                 if not isinstance(op, dict) or "op" not in op or "path" not in op:
                     raise ValueError("Invalid JSON Patch format: Missing 'op' or 'path'.")
        elif isinstance(patch, dict):
            pass

        return current_ooi.copy_to(
            PatchGenerated,
            patch=patch
        )

    @classmethod
    def transition_to_change_committed(
        cls,
        current_ooi: 'PatchGenerated',
        commit_hash: str
    ) -> 'ChangeCommitted':
        """Transition Factory Method: PatchGenerated -> ChangeCommitted."""
        if not isinstance(current_ooi, PatchGenerated):
            raise TypeError("Transition only allowed from PatchGenerated state.")

        if not commit_hash:
            raise ValueError("Commit hash cannot be empty.")

        return current_ooi.copy_to(
            ChangeCommitted,
            commit_hash=commit_hash
        )
