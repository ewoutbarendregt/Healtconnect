"""
Workflow state machine for document processing.
"""
from enum import Enum
from typing import Optional, Dict, Any

from ..utils.logging import get_logger


class WorkflowState(Enum):
    """Workflow states."""
    IDLE = "idle"
    NAVIGATING = "navigating"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    CONVERTING = "converting"
    UPLOADING = "uploading"
    FINALIZING = "finalizing"
    VERIFYING = "verifying"
    DELETING = "deleting"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowStateMachine:
    """Manages workflow state transitions."""

    # Valid state transitions
    TRANSITIONS = {
        WorkflowState.IDLE: [WorkflowState.NAVIGATING],
        WorkflowState.NAVIGATING: [WorkflowState.DOWNLOADING, WorkflowState.ERROR],
        WorkflowState.DOWNLOADING: [WorkflowState.EXTRACTING, WorkflowState.ERROR],
        WorkflowState.EXTRACTING: [WorkflowState.CONVERTING, WorkflowState.ERROR],
        WorkflowState.CONVERTING: [WorkflowState.UPLOADING, WorkflowState.ERROR],
        WorkflowState.UPLOADING: [WorkflowState.FINALIZING, WorkflowState.ERROR],
        WorkflowState.FINALIZING: [WorkflowState.VERIFYING, WorkflowState.ERROR],
        WorkflowState.VERIFYING: [WorkflowState.DELETING, WorkflowState.ERROR],
        WorkflowState.DELETING: [WorkflowState.COMPLETED, WorkflowState.ERROR],
        WorkflowState.COMPLETED: [],
        WorkflowState.ERROR: [WorkflowState.IDLE]  # Can restart from error
    }

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.current_state = WorkflowState.IDLE
        self.state_data: Dict[str, Any] = {}
        self.logger = get_logger(f"state_machine.{document_id}", document_id)

    def transition_to(self, new_state: WorkflowState, data: Optional[Dict[str, Any]] = None):
        """
        Transition to a new state.

        Args:
            new_state: The target state
            data: Optional data to store with the state

        Raises:
            ValueError: If the transition is invalid
        """
        if new_state not in self.TRANSITIONS.get(self.current_state, []):
            raise ValueError(
                f"Invalid transition from {self.current_state.value} to {new_state.value}"
            )

        self.logger.info(
            f"State transition: {self.current_state.value} -> {new_state.value}"
        )
        self.current_state = new_state

        if data:
            self.state_data.update(data)

    def get_state(self) -> WorkflowState:
        """Get the current state."""
        return self.current_state

    def get_data(self, key: str) -> Optional[Any]:
        """Get data stored in the state."""
        return self.state_data.get(key)

    def set_data(self, key: str, value: Any):
        """Store data in the state."""
        self.state_data[key] = value

    def is_completed(self) -> bool:
        """Check if the workflow is completed."""
        return self.current_state == WorkflowState.COMPLETED

    def is_error(self) -> bool:
        """Check if the workflow is in error state."""
        return self.current_state == WorkflowState.ERROR

    def reset(self):
        """Reset the state machine to idle."""
        self.current_state = WorkflowState.IDLE
        self.state_data = {}
        self.logger.info("State machine reset to IDLE")
