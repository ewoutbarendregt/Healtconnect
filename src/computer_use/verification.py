"""
Screenshot verification logic for UI automation.
"""
import asyncio
from pathlib import Path
from typing import Optional

import anthropic

from ..config import Config
from ..exceptions import VerificationError
from ..utils.logging import get_logger
from ..utils.screenshots import ScreenshotManager
from prompts.extraction_prompts import VERIFICATION_PROMPT


class ScreenshotVerifier:
    """Verifies UI actions using screenshot analysis."""

    def __init__(self, document_id: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.screenshot_manager = ScreenshotManager(document_id)
        self.logger = get_logger("verifier", document_id)

    async def verify_screenshot(
        self,
        screenshot_data: str,
        action: str,
        expected_result: str,
        step: str
    ) -> bool:
        """
        Verify that an action produced the expected result.

        Args:
            screenshot_data: Base64 encoded screenshot
            action: Description of the action taken
            expected_result: What should be visible
            step: Workflow step name

        Returns:
            True if verification passed

        Raises:
            VerificationError: If verification fails
        """
        self.logger.debug(f"Verifying: {action} -> {expected_result}")

        # Save screenshot
        screenshot_path = self.screenshot_manager.save_screenshot(
            screenshot_data,
            step,
            action
        )

        # Prepare verification prompt
        prompt = VERIFICATION_PROMPT.format(
            action=action,
            expected_result=expected_result
        )

        try:
            # Call Claude API with vision
            # Prepare image content
            if screenshot_data.startswith("data:image/png;base64,"):
                image_data = screenshot_data.split(",", 1)[1]
            else:
                image_data = screenshot_data

            response = self.client.messages.create(
                model=Config.MODEL_COMPUTER_USE,
                max_tokens=256,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            result = response.content[0].text.strip()
            self.logger.debug(f"Verification result: {result}")

            if result.startswith("PASS"):
                self.logger.info(f"Verification PASSED: {action}")
                return True
            else:
                error_msg = result.replace("FAIL:", "").strip()
                self.logger.error(f"Verification FAILED: {error_msg}")
                raise VerificationError(f"{action} failed: {error_msg}")

        except anthropic.APIError as e:
            raise VerificationError(f"API error during verification: {e}")
        except Exception as e:
            raise VerificationError(f"Unexpected error during verification: {e}")

    async def execute_with_verification(
        self,
        action_func,
        action_desc: str,
        expected_result: str,
        step: str,
        wait_time: float = 1.0
    ) -> any:
        """
        Execute an action and verify the result.

        Args:
            action_func: Async function that executes the action and returns screenshot
            action_desc: Description of the action
            expected_result: Expected result description
            step: Workflow step name
            wait_time: Time to wait after action before verification

        Returns:
            Result from action_func

        Raises:
            VerificationError: If verification fails
        """
        self.logger.info(f"Executing action: {action_desc}")

        # Execute action
        result = await action_func()

        # Wait for UI to update
        await asyncio.sleep(wait_time)

        # Get screenshot from result (expected to be a dict with 'screenshot' key)
        if isinstance(result, dict) and 'screenshot' in result:
            screenshot = result['screenshot']

            # Verify
            await self.verify_screenshot(
                screenshot,
                action_desc,
                expected_result,
                step
            )

        return result
