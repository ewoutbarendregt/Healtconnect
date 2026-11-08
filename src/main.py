"""
Main orchestrator for HealthConnect document automation.
"""
import asyncio
import sys
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from .config import Config
from .exceptions import (
    WorkflowError,
    VerificationError,
    StuckLoopError,
    SafetyError,
    ExtractionError,
    ConversionError
)
from .utils.logging import get_logger
from .utils.screenshots import ScreenshotManager
from .workflow import WorkflowState, WorkflowStateMachine, CheckpointManager
from .document_processor import MetadataExtractor, PDFConverter, NamingConvention
from .computer_use import ComputerUseAgent


class DocumentProcessor:
    """Main document processor orchestrator."""

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.logger = get_logger("orchestrator", document_id)
        self.screenshot_manager = ScreenshotManager(document_id)
        self.state_machine = WorkflowStateMachine(document_id)
        self.checkpoint_manager = CheckpointManager(document_id)

        # Processors
        self.extractor = MetadataExtractor()
        self.converter = PDFConverter()
        self.naming = NamingConvention()

        # Computer use agent
        self.agent = ComputerUseAgent(document_id)

    async def process_document(self, txt_file: Path) -> bool:
        """
        Process a single document through the complete workflow.

        Args:
            txt_file: Path to the text file to process

        Returns:
            True if processing successful

        Raises:
            WorkflowError: If processing fails
        """
        self.logger.step_start("process_document", file=txt_file.name)

        try:
            # Check if we can resume from checkpoint
            resume_step = self.checkpoint_manager.get_resume_step()
            if resume_step:
                self.logger.info(f"Resuming from checkpoint: {resume_step}")

            # Step 1: Download (if needed)
            if not self.checkpoint_manager.is_step_completed("download_complete"):
                await self._step_download(txt_file.name)
                self.checkpoint_manager.save_checkpoint("download_complete", {
                    "txt_file": str(txt_file)
                })

            # Step 2: Extract metadata
            if not self.checkpoint_manager.is_step_completed("metadata_extracted"):
                metadata = await self._step_extract_metadata(txt_file)
                self.checkpoint_manager.save_checkpoint("metadata_extracted", {
                    "metadata": metadata
                })
            else:
                metadata = self.checkpoint_manager.get_checkpoint_data("metadata")

            # Step 3: Convert to PDF
            if not self.checkpoint_manager.is_step_completed("pdf_converted"):
                pdf_path = await self._step_convert_to_pdf(txt_file, metadata)
                self.checkpoint_manager.save_checkpoint("pdf_converted", {
                    "pdf_path": str(pdf_path)
                })
            else:
                pdf_path = Path(self.checkpoint_manager.get_checkpoint_data("pdf_path"))

            # Step 4: Upload PDF
            if not self.checkpoint_manager.is_step_completed("upload_complete"):
                await self._step_upload_pdf(pdf_path, metadata)
                self.checkpoint_manager.save_checkpoint("upload_complete")

            # Step 5: Finalize contact
            await self._step_finalize_contact()

            # Step 6: Verify upload
            if not self.checkpoint_manager.is_step_completed("verification_passed"):
                await self._step_verify_upload(metadata)
                self.checkpoint_manager.save_checkpoint("verification_passed")

            # Step 7: Delete original
            if not self.checkpoint_manager.is_step_completed("original_deleted"):
                await self._step_delete_original(txt_file)
                self.checkpoint_manager.save_checkpoint("original_deleted")

            self.logger.step_complete("process_document", success=True)
            self.state_machine.transition_to(WorkflowState.COMPLETED)

            return True

        except WorkflowError as e:
            await self._handle_error(e, self.state_machine.get_state().value)
            raise
        except Exception as e:
            await self._handle_error(WorkflowError(str(e)), "unknown")
            raise

    async def _step_download(self, filename: str):
        """Step 1: Download file."""
        self.logger.step_start("download", filename=filename)
        self.state_machine.transition_to(WorkflowState.DOWNLOADING)

        try:
            downloaded_path = await self.agent.download_file(filename)

            # Verify file exists
            if not downloaded_path.exists():
                raise WorkflowError(f"Downloaded file not found: {downloaded_path}")

            self.logger.step_complete("download", success=True, path=str(downloaded_path))

        except Exception as e:
            self.logger.step_error("download", str(e))
            raise

    async def _step_extract_metadata(self, txt_file: Path) -> dict:
        """Step 2: Extract metadata."""
        self.logger.step_start("extract", file=txt_file.name)
        self.state_machine.transition_to(WorkflowState.EXTRACTING)

        try:
            metadata = self.extractor.extract_metadata(txt_file)

            # Validate metadata
            if not self.extractor.validate_metadata(metadata):
                raise ExtractionError("Metadata validation failed")

            self.logger.step_complete(
                "extract",
                success=True,
                type=metadata.get("document_type"),
                code=metadata.get("specialization_code")
            )

            return metadata

        except Exception as e:
            self.logger.step_error("extract", str(e))
            raise

    async def _step_convert_to_pdf(self, txt_file: Path, metadata: dict) -> Path:
        """Step 3: Convert to PDF."""
        self.logger.step_start("convert", file=txt_file.name)
        self.state_machine.transition_to(WorkflowState.CONVERTING)

        try:
            pdf_path = self.converter.convert_to_pdf(txt_file, metadata)

            # Verify PDF
            if not self.converter.verify_pdf(pdf_path):
                raise ConversionError("PDF verification failed")

            self.logger.step_complete("convert", success=True, pdf=pdf_path.name)

            return pdf_path

        except Exception as e:
            self.logger.step_error("convert", str(e))
            raise

    async def _step_upload_pdf(self, pdf_path: Path, metadata: dict):
        """Step 4: Upload PDF."""
        self.logger.step_start("upload", pdf=pdf_path.name)
        self.state_machine.transition_to(WorkflowState.UPLOADING)

        try:
            logical_name = metadata.get("logical_name")
            summary = metadata.get("summary")

            await self.agent.upload_pdf(pdf_path, logical_name, summary)

            self.logger.step_complete("upload", success=True)

        except Exception as e:
            self.logger.step_error("upload", str(e))
            raise

    async def _step_finalize_contact(self):
        """Step 5: Finalize contact."""
        self.logger.step_start("finalize")
        self.state_machine.transition_to(WorkflowState.FINALIZING)

        try:
            await self.agent.finalize_contact()

            self.logger.step_complete("finalize", success=True)

        except Exception as e:
            self.logger.step_error("finalize", str(e))
            raise

    async def _step_verify_upload(self, metadata: dict):
        """Step 6: Verify upload."""
        self.logger.step_start("verify")
        self.state_machine.transition_to(WorkflowState.VERIFYING)

        try:
            logical_name = metadata.get("logical_name")
            summary = metadata.get("summary")

            await self.agent.verify_upload(logical_name, summary)

            self.logger.step_complete("verify", success=True)

        except VerificationError as e:
            self.logger.step_error("verify", str(e))
            raise SafetyError(f"Upload verification failed: {e}")

    async def _step_delete_original(self, txt_file: Path):
        """Step 7: Delete original file."""
        self.logger.step_start("delete", file=txt_file.name)
        self.state_machine.transition_to(WorkflowState.DELETING)

        # Safety checks
        if not Config.REQUIRE_VERIFICATION:
            raise SafetyError("Cannot delete: verification is required")

        if not self.checkpoint_manager.is_step_completed("verification_passed"):
            raise SafetyError("Cannot delete: upload not verified")

        pdf_path = Path(self.checkpoint_manager.get_checkpoint_data("pdf_path"))
        if not pdf_path.exists():
            raise SafetyError("Cannot delete: PDF file not found")

        try:
            # Move to trash first (safer than immediate delete)
            trash_path = Config.TRASH_DIR / txt_file.name
            shutil.move(str(txt_file), str(trash_path))

            self.logger.info(f"Moved to trash: {txt_file.name}")
            self.logger.step_complete("delete", success=True)

        except Exception as e:
            self.logger.step_error("delete", str(e))
            raise

    async def _handle_error(self, error: WorkflowError, current_step: str):
        """
        Handle workflow errors.

        Args:
            error: The error that occurred
            current_step: Current workflow step
        """
        self.logger.error(f"Error in {current_step}: {error}")

        # Save error to checkpoint
        self.checkpoint_manager.save_error(current_step, str(error))

        # Transition to error state
        self.state_machine.transition_to(WorkflowState.ERROR)


class HealthConnectAutomation:
    """Main application orchestrator."""

    def __init__(self):
        self.logger = get_logger("main")
        Config.validate()

    async def process_all_documents(self) -> int:
        """
        Process all documents in the patient file.

        Returns:
            Number of documents successfully processed
        """
        self.logger.info("Starting document processing")

        agent = ComputerUseAgent()

        # Navigate to files and get list
        try:
            file_list = await agent.navigate_to_files()
            self.logger.info(f"Found {len(file_list)} files to process")

        except Exception as e:
            self.logger.error(f"Failed to get file list: {e}")
            return 0

        # Process each file
        success_count = 0
        for filename in file_list:
            if not filename.endswith('.txt'):
                continue

            document_id = Path(filename).stem
            self.logger.info(f"Processing document: {document_id}")

            processor = DocumentProcessor(document_id)

            try:
                # Check if file exists in downloads (already downloaded)
                txt_file = Config.DOWNLOAD_DIR / filename
                if not txt_file.exists():
                    # Will be downloaded by processor
                    txt_file = Config.DOWNLOAD_DIR / filename

                await processor.process_document(txt_file)
                success_count += 1

            except WorkflowError as e:
                self.logger.error(f"Failed to process {filename}: {e}")
                continue

        self.logger.info(f"Completed: {success_count}/{len(file_list)} documents processed")
        return success_count

    async def process_single_document(self, file_id: str) -> bool:
        """
        Process a single document.

        Args:
            file_id: Document identifier

        Returns:
            True if successful
        """
        self.logger.info(f"Processing single document: {file_id}")

        processor = DocumentProcessor(file_id)

        txt_file = Config.DOWNLOAD_DIR / f"{file_id}.txt"

        try:
            await processor.process_document(txt_file)
            return True

        except WorkflowError as e:
            self.logger.error(f"Failed to process document: {e}")
            return False

    async def resume_document(self, document_id: str) -> bool:
        """
        Resume processing a document from checkpoint.

        Args:
            document_id: Document identifier

        Returns:
            True if successful
        """
        self.logger.info(f"Resuming document: {document_id}")

        processor = DocumentProcessor(document_id)

        # Get txt file from checkpoint
        checkpoint_manager = CheckpointManager(document_id)
        checkpoint = checkpoint_manager.load_checkpoint()

        if not checkpoint:
            self.logger.error(f"No checkpoint found for {document_id}")
            return False

        txt_file = Path(checkpoint.get("data", {}).get("txt_file", ""))

        if not txt_file or not txt_file.exists():
            self.logger.error(f"Text file not found in checkpoint")
            return False

        try:
            await processor.process_document(txt_file)
            return True

        except WorkflowError as e:
            self.logger.error(f"Failed to resume document: {e}")
            return False

    def cleanup_trash(self, older_than_hours: int = None):
        """
        Permanently delete files from trash.

        Args:
            older_than_hours: Only delete files older than this many hours
        """
        if older_than_hours is None:
            older_than_hours = Config.DELETE_AFTER_HOURS

        self.logger.info(f"Cleaning up trash (older than {older_than_hours} hours)")

        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        deleted_count = 0

        for file_path in Config.TRASH_DIR.glob("*"):
            if file_path.is_file():
                # Check file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    self.logger.info(f"Permanently deleted: {file_path.name}")

        self.logger.info(f"Deleted {deleted_count} files from trash")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="HealthConnect Document Automation")
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="Run against simulation app"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run against production HealthConnect"
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Process a single document"
    )
    parser.add_argument(
        "--file-id",
        type=str,
        help="Document ID to process (with --single)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint"
    )
    parser.add_argument(
        "--document-id",
        type=str,
        help="Document ID to resume (with --resume)"
    )
    parser.add_argument(
        "--cleanup-trash",
        action="store_true",
        help="Cleanup trash folder"
    )

    args = parser.parse_args()

    # Set simulation mode
    if args.production:
        Config.USE_SIMULATION = False
    else:
        Config.USE_SIMULATION = True

    app = HealthConnectAutomation()

    if args.cleanup_trash:
        app.cleanup_trash()
        return

    if args.resume:
        if not args.document_id:
            print("Error: --document-id required with --resume")
            sys.exit(1)

        success = await app.resume_document(args.document_id)
        sys.exit(0 if success else 1)

    if args.single:
        if not args.file_id:
            print("Error: --file-id required with --single")
            sys.exit(1)

        success = await app.process_single_document(args.file_id)
        sys.exit(0 if success else 1)

    # Process all documents
    count = await app.process_all_documents()
    print(f"Processed {count} documents")


if __name__ == "__main__":
    asyncio.run(main())
