"""
Screenshot capture and management utilities.
"""
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import Config


class ScreenshotManager:
    """Manages screenshot capture and storage."""

    def __init__(self, document_id: Optional[str] = None):
        self.document_id = document_id
        self.screenshot_dir = Config.LOG_DIR / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def save_screenshot(
        self,
        screenshot_data: str,
        step: str,
        action: Optional[str] = None,
        suffix: str = ""
    ) -> Path:
        """
        Save a screenshot to disk.

        Args:
            screenshot_data: Base64 encoded screenshot data
            step: The workflow step name
            action: Optional action description
            suffix: Optional suffix for the filename

        Returns:
            Path to the saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # Build filename
        parts = []
        if self.document_id:
            parts.append(self.document_id)
        parts.append(step)
        if action:
            parts.append(action.replace(" ", "_"))
        if suffix:
            parts.append(suffix)
        parts.append(timestamp)

        filename = "_".join(parts) + ".png"
        filepath = self.screenshot_dir / filename

        # Decode and save
        if screenshot_data.startswith("data:image/png;base64,"):
            screenshot_data = screenshot_data.split(",", 1)[1]

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(screenshot_data))

        return filepath

    def save_error_screenshot(
        self,
        screenshot_data: str,
        step: str,
        error_type: str
    ) -> Path:
        """
        Save a screenshot when an error occurs.

        Args:
            screenshot_data: Base64 encoded screenshot data
            step: The workflow step name
            error_type: Type of error that occurred

        Returns:
            Path to the saved screenshot
        """
        return self.save_screenshot(
            screenshot_data,
            step,
            action="error",
            suffix=error_type
        )

    def get_latest_screenshot(self, step: Optional[str] = None) -> Optional[Path]:
        """
        Get the path to the most recent screenshot.

        Args:
            step: Optional step name to filter by

        Returns:
            Path to the latest screenshot, or None if not found
        """
        pattern = "*"
        if self.document_id:
            pattern = f"{self.document_id}_*"
        if step:
            pattern = f"{self.document_id}_{step}_*" if self.document_id else f"{step}_*"

        screenshots = sorted(self.screenshot_dir.glob(f"{pattern}.png"), reverse=True)
        return screenshots[0] if screenshots else None
