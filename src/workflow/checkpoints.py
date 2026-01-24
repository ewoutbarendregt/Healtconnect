"""
Checkpoint management for crash recovery.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..config import Config


class CheckpointManager:
    """Manages workflow checkpoints for recovery."""

    CHECKPOINT_STEPS = [
        "download_complete",
        "metadata_extracted",
        "pdf_converted",
        "upload_complete",
        "verification_passed",
        "original_deleted"
    ]

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.checkpoint_file = Config.CHECKPOINT_DIR / f"{document_id}.json"

    def save_checkpoint(self, step: str, data: Optional[Dict[str, Any]] = None):
        """
        Save a checkpoint for the current document.

        Args:
            step: The completed workflow step
            data: Optional additional data to store
        """
        checkpoint = {
            "document_id": self.document_id,
            "completed_step": step,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

        # Load existing checkpoint if it exists
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, "r") as f:
                existing = json.load(f)
                # Merge data
                if "data" in existing:
                    checkpoint["data"].update(existing["data"])
                    checkpoint["data"].update(data or {})

        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoint, f, indent=2)

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load the checkpoint for the current document.

        Returns:
            Checkpoint data if exists, None otherwise
        """
        if not self.checkpoint_file.exists():
            return None

        with open(self.checkpoint_file, "r") as f:
            return json.load(f)

    def get_resume_step(self) -> Optional[str]:
        """
        Get the step to resume from.

        Returns:
            The next step to execute, or None if starting fresh
        """
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return None

        completed_step = checkpoint.get("completed_step")
        if not completed_step:
            return None

        # Find the index of the completed step
        try:
            step_index = self.CHECKPOINT_STEPS.index(completed_step)
            # Return the next step if available
            if step_index < len(self.CHECKPOINT_STEPS) - 1:
                return self.CHECKPOINT_STEPS[step_index + 1]
            # All steps completed
            return "completed"
        except ValueError:
            # Unknown step, start from beginning
            return None

    def is_step_completed(self, step: str) -> bool:
        """
        Check if a specific step has been completed.

        Args:
            step: The step name to check

        Returns:
            True if the step is completed
        """
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return False

        completed_step = checkpoint.get("completed_step")
        if not completed_step or completed_step not in self.CHECKPOINT_STEPS:
            return False

        try:
            completed_index = self.CHECKPOINT_STEPS.index(completed_step)
            step_index = self.CHECKPOINT_STEPS.index(step)
            return step_index <= completed_index
        except ValueError:
            return False

    def get_checkpoint_data(self, key: str) -> Optional[Any]:
        """
        Get data from the checkpoint.

        Args:
            key: The data key to retrieve

        Returns:
            The data value if exists, None otherwise
        """
        checkpoint = self.load_checkpoint()
        if not checkpoint or "data" not in checkpoint:
            return None
        return checkpoint["data"].get(key)

    def clear_checkpoint(self):
        """Clear the checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def save_error(self, step: str, error: str, screenshot_path: Optional[str] = None):
        """
        Save error information to the checkpoint.

        Args:
            step: The step where the error occurred
            error: Error description
            screenshot_path: Optional path to error screenshot
        """
        error_data = {
            "error_step": step,
            "error_message": error,
            "error_timestamp": datetime.now().isoformat()
        }
        if screenshot_path:
            error_data["error_screenshot"] = screenshot_path

        self.save_checkpoint(f"error_{step}", error_data)
