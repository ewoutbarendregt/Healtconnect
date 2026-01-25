"""
Metadata extraction from medical documents using Claude API.
"""
import json
from pathlib import Path
from typing import Dict, Any

import anthropic

from ..config import Config
from ..exceptions import ExtractionError
from ..utils.logging import get_logger


class MetadataExtractor:
    """Extracts metadata from medical documents using Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.logger = get_logger("extractor")

    def extract_metadata(self, document_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a medical document.

        Args:
            document_path: Path to the text document

        Returns:
            Dictionary containing extracted metadata

        Raises:
            ExtractionError: If extraction fails
        """
        self.logger.info(f"Extracting metadata from {document_path.name}")

        # Read document content
        try:
            with open(document_path, "r", encoding="utf-8") as f:
                document_content = f.read()
        except Exception as e:
            raise ExtractionError(f"Failed to read document: {e}")

        # Load extraction prompt
        from prompts.extraction_prompts import EXTRACTION_PROMPT

        prompt = EXTRACTION_PROMPT.format(document_content=document_content)

        # Call Claude API
        try:
            response = self.client.messages.create(
                model=Config.MODEL_EXTRACTION,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            response_text = response.content[0].text
            self.logger.debug(f"Claude response: {response_text}")

            # Extract JSON from response
            metadata = json.loads(response_text)

            # Validate required fields
            required_fields = [
                "document_type",
                "specialization_code",
                "specialist_name",
                "direction",
                "summary",
                "logical_name"
            ]

            for field in required_fields:
                if field not in metadata:
                    raise ExtractionError(f"Missing required field: {field}")

            self.logger.info(
                f"Extracted metadata: type={metadata['document_type']}, "
                f"code={metadata['specialization_code']}, "
                f"name={metadata['specialist_name']}, "
                f"logical_name={metadata['logical_name']}"
            )

            return metadata

        except json.JSONDecodeError as e:
            raise ExtractionError(f"Failed to parse JSON response: {e}")
        except anthropic.APIError as e:
            raise ExtractionError(f"Claude API error: {e}")
        except Exception as e:
            raise ExtractionError(f"Unexpected error during extraction: {e}")

    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate extracted metadata.

        Args:
            metadata: The metadata dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Check document type
        valid_types = [
            "specialistenbrief",
            "patiëntbrief",
            "verwijsbrief",
            "afspraakbericht",
            "aanvraagformulier"
        ]
        if metadata.get("document_type") not in valid_types:
            self.logger.warning(f"Invalid document type: {metadata.get('document_type')}")
            return False

        # Check specialization code
        valid_codes = set(Config.SPECIALIZATION_CODES.values())
        if metadata.get("specialization_code") not in valid_codes:
            self.logger.warning(
                f"Invalid specialization code: {metadata.get('specialization_code')}"
            )
            return False

        # Check summary length
        summary = metadata.get("summary", "")
        if len(summary) > 150:
            self.logger.warning(f"Summary too long: {len(summary)} characters")
            return False

        # Check direction
        if metadata.get("direction") not in ["incoming", "outgoing"]:
            self.logger.warning(f"Invalid direction: {metadata.get('direction')}")
            return False

        return True
