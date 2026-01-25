"""
Computer use agent for UI automation.
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

import anthropic

from ..config import Config
from ..exceptions import StuckLoopError, VerificationError, UploadError
from ..utils.logging import get_logger
from ..utils.screenshots import ScreenshotManager
from .verification import ScreenshotVerifier
from . import prompts


class ComputerUseAgent:
    """Agent that uses Claude's computer use capabilities to interact with UI."""

    def __init__(self, document_id: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.document_id = document_id
        self.logger = get_logger("computer_use_agent", document_id)
        self.screenshot_manager = ScreenshotManager(document_id)
        self.verifier = ScreenshotVerifier(document_id)
        self.action_history: List[str] = []
        self.iteration_count = 0

    def reset_iteration_count(self):
        """Reset iteration counter for a new step."""
        self.iteration_count = 0
        self.action_history = []

    def check_stuck_loop(self) -> bool:
        """
        Detect if the agent is stuck in a loop.

        Returns:
            True if stuck (last 3 actions are identical)
        """
        if len(self.action_history) < 3:
            return False

        return (
            self.action_history[-1] == self.action_history[-2] == self.action_history[-3]
        )

    def add_action(self, action: str):
        """
        Add an action to the history.

        Args:
            action: Description of the action

        Raises:
            StuckLoopError: If stuck in a loop
        """
        self.action_history.append(action)
        self.iteration_count += 1

        # Check for stuck loop
        if self.check_stuck_loop():
            raise StuckLoopError(
                f"Stuck in loop. Last 3 actions: {self.action_history[-3:]}"
            )

        # Check iteration limit
        if self.iteration_count >= Config.MAX_ITERATIONS_PER_STEP:
            raise StuckLoopError(
                f"Exceeded maximum iterations ({Config.MAX_ITERATIONS_PER_STEP}) for step"
            )

    async def execute_task(
        self,
        prompt: str,
        step: str,
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        Execute a computer use task.

        Args:
            prompt: The task prompt
            step: Workflow step name
            timeout: Optional timeout in seconds

        Returns:
            Result dictionary with status and data

        Raises:
            StuckLoopError: If agent gets stuck
            VerificationError: If verification fails
        """
        if timeout is None:
            timeout = Config.STEP_TIMEOUT_SECONDS

        self.reset_iteration_count()
        self.logger.info(f"Executing computer use task for step: {step}")

        try:
            # For this implementation, we'll use a simplified approach
            # In a real implementation, you would call the Anthropic API
            # with computer use tools enabled

            response = self.client.messages.create(
                model=Config.MODEL_COMPUTER_USE,
                max_tokens=4096,
                tools=[
                    {
                        "type": "computer_20241022",
                        "name": "computer",
                        "display_width_px": Config.SCREEN_WIDTH,
                        "display_height_px": Config.SCREEN_HEIGHT,
                        "display_number": 1
                    },
                    {
                        "type": "bash_20241022",
                        "name": "bash"
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Process response and handle tool use
            result = await self._process_response(response, step)

            return {
                "status": "success",
                "data": result
            }

        except StuckLoopError:
            raise
        except VerificationError:
            raise
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _process_response(
        self,
        response: anthropic.types.Message,
        step: str
    ) -> Dict[str, Any]:
        """
        Process the API response and handle tool calls.

        Args:
            response: The API response
            step: Workflow step name

        Returns:
            Result data
        """
        result = {}

        for content in response.content:
            if content.type == "tool_use":
                self.add_action(f"{content.name}: {content.input}")

                # Handle tool use
                if content.name == "computer":
                    # Computer interaction
                    action = content.input.get("action")
                    self.logger.debug(f"Computer action: {action}")

                    # In a real implementation, this would interact with the
                    # computer use API and capture screenshots

                elif content.name == "bash":
                    # Bash command
                    command = content.input.get("command")
                    self.logger.debug(f"Bash command: {command}")

            elif content.type == "text":
                # Text response
                result["text"] = content.text

        return result

    async def navigate_to_files(self) -> List[str]:
        """
        Navigate to patient files and identify .txt files.

        Returns:
            List of .txt filenames found

        Raises:
            StuckLoopError: If navigation fails
        """
        self.logger.info("Navigating to patient files")

        result = await self.execute_task(
            prompts.NAVIGATE_TO_PATIENT_FILES_PROMPT,
            "navigate"
        )

        # Extract file list from result
        # This is a simplified implementation
        # In reality, you would parse the result to get the actual file list
        return result.get("data", {}).get("files", [])

    async def download_file(self, filename: str) -> Path:
        """
        Download a specific file.

        Args:
            filename: Name of the file to download

        Returns:
            Path to the downloaded file

        Raises:
            StuckLoopError: If download fails
        """
        self.logger.info(f"Downloading file: {filename}")

        prompt = prompts.DOWNLOAD_FILE_PROMPT.format(filename=filename)

        result = await self.execute_task(prompt, "download")

        # Return path to downloaded file
        return Config.DOWNLOAD_DIR / filename

    async def upload_pdf(
        self,
        pdf_path: Path,
        logical_name: str,
        summary: str
    ) -> bool:
        """
        Upload a PDF file with metadata.

        Args:
            pdf_path: Path to the PDF file
            logical_name: Logical name for the document
            summary: Document summary

        Returns:
            True if upload successful

        Raises:
            UploadError: If upload fails
        """
        self.logger.info(f"Uploading PDF: {pdf_path.name}")

        prompt = prompts.UPLOAD_PDF_PROMPT.format(
            pdf_path=str(pdf_path),
            logical_name=logical_name,
            summary=summary
        )

        result = await self.execute_task(prompt, "upload")

        if result.get("status") != "success":
            raise UploadError(f"Upload failed: {result.get('error')}")

        return True

    async def finalize_contact(self) -> bool:
        """
        Finalize contact with no financial processing.

        Returns:
            True if finalization successful

        Raises:
            UploadError: If finalization fails
        """
        self.logger.info("Finalizing contact")

        result = await self.execute_task(
            prompts.FINALIZE_CONTACT_PROMPT,
            "finalize"
        )

        if result.get("status") != "success":
            raise UploadError(f"Finalization failed: {result.get('error')}")

        return True

    async def verify_upload(
        self,
        logical_name: str,
        summary: str
    ) -> bool:
        """
        Verify that upload completed successfully.

        Args:
            logical_name: Expected logical name
            summary: Expected summary

        Returns:
            True if verification passed

        Raises:
            VerificationError: If verification fails
        """
        self.logger.info("Verifying upload")

        prompt = prompts.VERIFY_UPLOAD_PROMPT.format(
            logical_name=logical_name,
            summary=summary
        )

        result = await self.execute_task(prompt, "verify")

        # Check for "VERIFIED" in response
        response_text = result.get("data", {}).get("text", "")
        if "VERIFIED" in response_text:
            self.logger.info("Upload verification passed")
            return True
        else:
            raise VerificationError(f"Upload verification failed: {response_text}")

    async def delete_original(self, filename: str) -> bool:
        """
        Delete the original text file.

        Args:
            filename: Name of the file to delete

        Returns:
            True if deletion successful

        Raises:
            StuckLoopError: If deletion fails
        """
        self.logger.info(f"Deleting original file: {filename}")

        prompt = prompts.DELETE_ORIGINAL_FILE_PROMPT.format(filename=filename)

        result = await self.execute_task(prompt, "delete")

        if result.get("status") != "success":
            self.logger.warning(f"Deletion failed: {result.get('error')}")
            return False

        return True
