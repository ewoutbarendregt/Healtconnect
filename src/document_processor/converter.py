"""
Text to PDF conversion with proper Dutch character encoding.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

from ..config import Config
from ..exceptions import ConversionError
from ..utils.logging import get_logger


class PDFConverter:
    """Converts text files to PDF with proper formatting."""

    def __init__(self):
        self.logger = get_logger("converter")

    def convert_to_pdf(
        self,
        txt_path: Path,
        metadata: Dict[str, Any],
        output_dir: Path = None
    ) -> Path:
        """
        Convert text file to PDF with proper encoding.

        Args:
            txt_path: Path to the text file
            metadata: Document metadata
            output_dir: Optional output directory (defaults to Config.PROCESSED_DIR)

        Returns:
            Path to the generated PDF file

        Raises:
            ConversionError: If conversion fails
        """
        if output_dir is None:
            output_dir = Config.PROCESSED_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        logical_name = metadata.get("logical_name", "document")
        date_str = datetime.now().strftime("%Y%m%d")
        pdf_filename = f"{logical_name}_{date_str}.pdf"
        pdf_path = output_dir / pdf_filename

        self.logger.info(f"Converting {txt_path.name} to {pdf_filename}")

        try:
            # Read text content
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Create PDF
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # Create styles
            styles = getSampleStyleSheet()

            # Custom style for body text
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT,
                spaceAfter=6
            )

            # Custom style for title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                leading=18,
                spaceAfter=12
            )

            # Build content
            story = []

            # Add title if document type is available
            if metadata.get("document_type"):
                title = Paragraph(
                    metadata["document_type"].capitalize(),
                    title_style
                )
                story.append(title)
                story.append(Spacer(1, 0.5*cm))

            # Add summary if available
            if metadata.get("summary"):
                summary_para = Paragraph(
                    f"<b>Samenvatting:</b> {metadata['summary']}",
                    body_style
                )
                story.append(summary_para)
                story.append(Spacer(1, 0.5*cm))

            # Add document content
            # Split content into paragraphs
            paragraphs = content.split('\n')
            for para in paragraphs:
                if para.strip():
                    # Escape XML special characters
                    para_text = (para
                                .replace('&', '&amp;')
                                .replace('<', '&lt;')
                                .replace('>', '&gt;'))
                    p = Paragraph(para_text, body_style)
                    story.append(p)
                else:
                    story.append(Spacer(1, 0.2*cm))

            # Build PDF
            doc.build(story)

            self.logger.info(f"PDF created successfully: {pdf_path}")
            return pdf_path

        except Exception as e:
            raise ConversionError(f"Failed to convert document to PDF: {e}")

    def verify_pdf(self, pdf_path: Path) -> bool:
        """
        Verify that the PDF file was created successfully.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if valid, False otherwise
        """
        if not pdf_path.exists():
            self.logger.error(f"PDF file does not exist: {pdf_path}")
            return False

        # Check file size
        file_size = pdf_path.stat().st_size
        if file_size < 100:  # Minimum reasonable PDF size
            self.logger.error(f"PDF file too small: {file_size} bytes")
            return False

        # Check file extension
        if pdf_path.suffix.lower() != '.pdf':
            self.logger.error(f"Invalid file extension: {pdf_path.suffix}")
            return False

        self.logger.info(f"PDF verification passed: {pdf_path.name}")
        return True
