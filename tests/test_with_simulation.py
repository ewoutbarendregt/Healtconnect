"""
Integration tests with simulation app.
"""
import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.document_processor import MetadataExtractor, PDFConverter, NamingConvention
from src.workflow import CheckpointManager, WorkflowState, WorkflowStateMachine


@pytest.fixture
def sample_txt_file(tmp_path):
    """Create a sample text file for testing."""
    content = """
SPECIALISTENBRIEF NEUROLOGIE

Van: Dr. J. Stam, Neuroloog
Aan: Huisarts

Betreft: Controle Multiple Sclerose

Geachte collega,

Patiënt bezocht mij op de polikliniek voor controle van de bekende Multiple Sclerose.

BEVINDINGEN:
Het klinisch beeld is stabiel. Geen nieuwe uitvalsverschijnselen.
MRI toont geen nieuwe laesies.

BELEID:
Voortzetting huidige medicatie (Interferon beta-1a).
Volgende controle over 6 maanden.

Met vriendelijke groet,
Dr. J. Stam
Neuroloog
""".strip()

    txt_file = tmp_path / "test_document.txt"
    txt_file.write_text(content, encoding="utf-8")
    return txt_file


class TestMetadataExtraction:
    """Test metadata extraction."""

    def test_extractor_initialization(self):
        """Test extractor can be initialized."""
        extractor = MetadataExtractor()
        assert extractor is not None

    @pytest.mark.skipif(not Config.ANTHROPIC_API_KEY, reason="API key not set")
    def test_extract_metadata(self, sample_txt_file):
        """Test metadata extraction from document."""
        extractor = MetadataExtractor()

        metadata = extractor.extract_metadata(sample_txt_file)

        # Verify required fields
        assert "document_type" in metadata
        assert "specialization_code" in metadata
        assert "specialist_name" in metadata
        assert "direction" in metadata
        assert "summary" in metadata
        assert "logical_name" in metadata

        # Verify values make sense
        assert metadata["document_type"] in [
            "specialistenbrief",
            "patiëntbrief",
            "verwijsbrief",
            "afspraakbericht",
            "aanvraagformulier"
        ]
        assert len(metadata["specialization_code"]) == 3
        assert len(metadata["summary"]) <= 150

    def test_validate_metadata(self):
        """Test metadata validation."""
        extractor = MetadataExtractor()

        valid_metadata = {
            "document_type": "specialistenbrief",
            "specialization_code": "NEU",
            "specialist_name": "Stam",
            "direction": "incoming",
            "summary": "Stabiel klinisch beeld, voortzetting medicatie.",
            "logical_name": "NEU.Stam"
        }

        assert extractor.validate_metadata(valid_metadata) is True

        # Test invalid type
        invalid_metadata = valid_metadata.copy()
        invalid_metadata["document_type"] = "invalid_type"
        assert extractor.validate_metadata(invalid_metadata) is False

        # Test invalid code
        invalid_metadata = valid_metadata.copy()
        invalid_metadata["specialization_code"] = "XXX"
        assert extractor.validate_metadata(invalid_metadata) is False


class TestPDFConversion:
    """Test PDF conversion."""

    def test_converter_initialization(self):
        """Test converter can be initialized."""
        converter = PDFConverter()
        assert converter is not None

    def test_convert_to_pdf(self, sample_txt_file, tmp_path):
        """Test text to PDF conversion."""
        converter = PDFConverter()

        metadata = {
            "document_type": "specialistenbrief",
            "specialization_code": "NEU",
            "specialist_name": "Stam",
            "direction": "incoming",
            "summary": "Stabiel klinisch beeld, voortzetting medicatie.",
            "logical_name": "NEU.Stam"
        }

        pdf_path = converter.convert_to_pdf(sample_txt_file, metadata, tmp_path)

        # Verify PDF exists
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"

        # Verify file size
        assert pdf_path.stat().st_size > 100

    def test_verify_pdf(self, sample_txt_file, tmp_path):
        """Test PDF verification."""
        converter = PDFConverter()

        metadata = {
            "document_type": "specialistenbrief",
            "specialization_code": "NEU",
            "specialist_name": "Stam",
            "direction": "incoming",
            "summary": "Stabiel klinisch beeld.",
            "logical_name": "NEU.Stam"
        }

        pdf_path = converter.convert_to_pdf(sample_txt_file, metadata, tmp_path)

        assert converter.verify_pdf(pdf_path) is True

        # Test non-existent file
        fake_path = tmp_path / "nonexistent.pdf"
        assert converter.verify_pdf(fake_path) is False


class TestNamingConvention:
    """Test naming convention logic."""

    def test_naming_initialization(self):
        """Test naming can be initialized."""
        naming = NamingConvention()
        assert naming is not None

    def test_generate_logical_name_incoming(self):
        """Test logical name generation for incoming documents."""
        naming = NamingConvention()

        metadata = {
            "specialization_code": "NEU",
            "specialist_name": "Stam",
            "direction": "incoming",
            "document_type": "specialistenbrief"
        }

        logical_name = naming.generate_logical_name(metadata)
        assert logical_name == "NEU.Stam"

    def test_generate_logical_name_outgoing(self):
        """Test logical name generation for outgoing documents."""
        naming = NamingConvention()

        metadata = {
            "specialization_code": "NEU",
            "specialist_name": "Stam",
            "direction": "outgoing",
            "document_type": "verwijsbrief"
        }

        logical_name = naming.generate_logical_name(metadata)
        assert logical_name == "NEU.Huisarts"

    def test_validate_logical_name(self):
        """Test logical name validation."""
        naming = NamingConvention()

        # Valid names
        assert naming.validate_logical_name("NEU.Stam") is True
        assert naming.validate_logical_name("LON.BovenIJ") is True
        assert naming.validate_logical_name("CAR.Huisarts") is True

        # Invalid names
        assert naming.validate_logical_name("NEURO.Stam") is False  # Code too long
        assert naming.validate_logical_name("XXX.Stam") is False  # Invalid code
        assert naming.validate_logical_name("NEUStam") is False  # Missing dot
        assert naming.validate_logical_name("NEU.") is False  # Empty name


class TestCheckpointManager:
    """Test checkpoint management."""

    def test_checkpoint_initialization(self):
        """Test checkpoint manager can be initialized."""
        checkpoint_manager = CheckpointManager("test_doc_123")
        assert checkpoint_manager is not None

    def test_save_and_load_checkpoint(self, tmp_path):
        """Test saving and loading checkpoints."""
        # Temporarily override checkpoint directory
        original_checkpoint_dir = Config.CHECKPOINT_DIR
        Config.CHECKPOINT_DIR = tmp_path

        try:
            checkpoint_manager = CheckpointManager("test_doc_123")

            # Save checkpoint
            checkpoint_manager.save_checkpoint("download_complete", {
                "txt_file": "/path/to/file.txt"
            })

            # Load checkpoint
            checkpoint = checkpoint_manager.load_checkpoint()

            assert checkpoint is not None
            assert checkpoint["completed_step"] == "download_complete"
            assert checkpoint["data"]["txt_file"] == "/path/to/file.txt"

        finally:
            Config.CHECKPOINT_DIR = original_checkpoint_dir

    def test_is_step_completed(self, tmp_path):
        """Test checking if step is completed."""
        original_checkpoint_dir = Config.CHECKPOINT_DIR
        Config.CHECKPOINT_DIR = tmp_path

        try:
            checkpoint_manager = CheckpointManager("test_doc_123")

            # No checkpoint yet
            assert checkpoint_manager.is_step_completed("download_complete") is False

            # Save checkpoint
            checkpoint_manager.save_checkpoint("metadata_extracted")

            # Check steps
            assert checkpoint_manager.is_step_completed("download_complete") is True
            assert checkpoint_manager.is_step_completed("metadata_extracted") is True
            assert checkpoint_manager.is_step_completed("pdf_converted") is False

        finally:
            Config.CHECKPOINT_DIR = original_checkpoint_dir


class TestWorkflowStateMachine:
    """Test workflow state machine."""

    def test_state_machine_initialization(self):
        """Test state machine can be initialized."""
        state_machine = WorkflowStateMachine("test_doc_123")
        assert state_machine.get_state() == WorkflowState.IDLE

    def test_state_transitions(self):
        """Test valid state transitions."""
        state_machine = WorkflowStateMachine("test_doc_123")

        # Valid transition
        state_machine.transition_to(WorkflowState.NAVIGATING)
        assert state_machine.get_state() == WorkflowState.NAVIGATING

        state_machine.transition_to(WorkflowState.DOWNLOADING)
        assert state_machine.get_state() == WorkflowState.DOWNLOADING

    def test_invalid_state_transition(self):
        """Test invalid state transitions raise error."""
        state_machine = WorkflowStateMachine("test_doc_123")

        # Invalid transition
        with pytest.raises(ValueError):
            state_machine.transition_to(WorkflowState.COMPLETED)

    def test_state_data(self):
        """Test storing data in state."""
        state_machine = WorkflowStateMachine("test_doc_123")

        state_machine.set_data("test_key", "test_value")
        assert state_machine.get_data("test_key") == "test_value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow_simulation():
    """
    Integration test with simulation app.

    This test requires the simulation app to be running.
    Run with: pytest tests/test_with_simulation.py -m integration -v
    """
    # This test would interact with the simulation app
    # For now, it's a placeholder

    # TODO: Implement full workflow test when simulation app is running
    pytest.skip("Integration test requires running simulation app")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
