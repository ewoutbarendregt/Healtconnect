"""
Naming convention logic for HealthConnect documents.
"""
from typing import Dict, Any

from ..config import Config
from ..utils.logging import get_logger


class NamingConvention:
    """Handles logical naming for HealthConnect documents."""

    def __init__(self):
        self.logger = get_logger("naming")

    def generate_logical_name(self, metadata: Dict[str, Any]) -> str:
        """
        Generate logical name based on metadata.

        Format:
        - Incoming specialist letter: [CODE].[SpecialistLastName]
        - Incoming from hospital: [CODE].[Hospital]
        - Outgoing referral: [CODE].Huisarts
        - Follow-up letter: [CODE].[Name] follow-up

        Args:
            metadata: Document metadata

        Returns:
            Logical name string
        """
        code = metadata.get("specialization_code", "UNK")
        direction = metadata.get("direction", "incoming")
        specialist_name = metadata.get("specialist_name", "Unknown")
        document_type = metadata.get("document_type", "")

        # For outgoing documents
        if direction == "outgoing":
            logical_name = f"{code}.Huisarts"

        # For incoming documents
        else:
            # Check if it's a follow-up
            if "follow-up" in document_type.lower() or "controle" in document_type.lower():
                logical_name = f"{code}.{specialist_name} follow-up"
            else:
                logical_name = f"{code}.{specialist_name}"

        self.logger.info(f"Generated logical name: {logical_name}")
        return logical_name

    def validate_logical_name(self, logical_name: str) -> bool:
        """
        Validate logical name format.

        Args:
            logical_name: The logical name to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic format check: CODE.Name
        if '.' not in logical_name:
            self.logger.warning(f"Invalid format (missing dot): {logical_name}")
            return False

        parts = logical_name.split('.', 1)
        if len(parts) != 2:
            self.logger.warning(f"Invalid format (wrong number of parts): {logical_name}")
            return False

        code, name = parts

        # Check code length
        if len(code) != 3:
            self.logger.warning(f"Invalid code length: {code}")
            return False

        # Check code is valid
        valid_codes = set(Config.SPECIALIZATION_CODES.values())
        if code not in valid_codes:
            self.logger.warning(f"Invalid specialization code: {code}")
            return False

        # Check name is not empty
        if not name or not name.strip():
            self.logger.warning(f"Empty name in logical name: {logical_name}")
            return False

        self.logger.debug(f"Logical name validated: {logical_name}")
        return True

    def sanitize_name(self, name: str) -> str:
        """
        Sanitize a name for use in logical name.

        Args:
            name: The name to sanitize

        Returns:
            Sanitized name
        """
        # Remove special characters that might cause issues
        # Keep letters, numbers, spaces, hyphens, and dots
        sanitized = ''.join(
            c for c in name
            if c.isalnum() or c in ' .-'
        )

        # Remove leading/trailing whitespace
        sanitized = sanitized.strip()

        # Collapse multiple spaces
        sanitized = ' '.join(sanitized.split())

        return sanitized
