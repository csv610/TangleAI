"""
Base module for PDF operations.
"""
from pathlib import Path
import PyPDF2

class PDFBase:
    """
    A base class for PDF operations.
    """

    def __init__(self):
        """
        Initialize the PDFBase.
        """
        pass

    def _validate_pdf_path(self, file_path: str) -> Path:
        """
        Validate that the given file path is a valid PDF file.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            Path: Validated Path object

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a PDF
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        if not self._is_pdf(pdf_path):
            raise ValueError(f"File is not a PDF: {pdf_path}")
        return pdf_path

    def _is_pdf(self, file_path: Path) -> bool:
        """
        Checks if the given file path points to a PDF file.
        """
        return file_path.suffix.lower() == '.pdf'

    def get_page_count(self, input_pdf: str) -> int:
        """
        Get the total number of pages in the PDF.

        Args:
            input_pdf (str): Path to the input PDF file

        Returns:
            int: Total number of pages
        """
        try:
            pdf_path = self._validate_pdf_path(input_pdf)
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                return len(pdf_reader.pages)
        except PyPDF2.PdfReadError as e:
            raise Exception(f"Error reading PDF file: {e}")
        except Exception as e:
            raise Exception(f"Error processing PDF: {e}")

    def get_info(self, input_pdf: str) -> dict:
        """
        Get information about the PDF file.

        Args:
            input_pdf (str): Path to the input PDF file

        Returns:
            dict: Dictionary containing PDF metadata and page count
        """
        try:
            pdf_path = self._validate_pdf_path(input_pdf)
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                metadata = pdf_reader.metadata
                total_pages = len(pdf_reader.pages)
                return {
                    'filename': pdf_path.name,
                    'total_pages': total_pages,
                    'title': metadata.get('/Title', 'N/A') if metadata else 'N/A',
                    'author': metadata.get('/Author', 'N/A') if metadata else 'N/A',
                    'subject': metadata.get('/Subject', 'N/A') if metadata else 'N/A'
                }
        except PyPDF2.PdfReadError as e:
            raise Exception(f"Error reading PDF file: {e}")
        except Exception as e:
            raise Exception(f"Error processing PDF: {e}")
