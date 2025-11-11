"""
Module for splitting PDF files by page range.
"""
from typing import Optional, List
from pathlib import Path
from pdf_base import PDFBase
import PyPDF2
import argparse

class PDFSplitter(PDFBase):
    """
    A class for splitting PDF files by page range.
    """

    def __init__(self):
        """
        Initialize the PDFSplitter.
        """
        super().__init__()



    def validate_page_range(self, start_page: int, end_page: int, total_pages: int) -> tuple:
        """
        Validate and adjust the page range.

        Args:
            start_page (int): Starting page number (1-indexed)
            end_page (int): Ending page number (1-indexed, inclusive)

        Returns:
            tuple: (adjusted_start_page, adjusted_end_page)

        Raises:
            ValueError: If page range is invalid
        """
        # Ensure start_page is at least 1: min = max(1, user_start_page)
        adjusted_start_page = max(1, start_page)

        # Warn user if start_page was adjusted
        if start_page < 1:
            print(f"Warning: start_page ({start_page}) is less than 1. Using {adjusted_start_page} instead.")

        # Cap end_page to the maximum available pages: max = min(user_end_page, pdf_total_pages)
        adjusted_end_page = min(end_page, total_pages)

        # Warn user if end_page was capped
        if end_page > total_pages:
            print(f"Warning: end_page ({end_page}) exceeds total pages ({total_pages}). Using {adjusted_end_page} instead.")

        # Validate that adjusted start_page doesn't exceed total pages
        if adjusted_start_page > total_pages:
            raise ValueError(f"start_page ({adjusted_start_page}) exceeds total pages ({total_pages})")

        # Validate that start_page doesn't exceed end_page after adjustments
        if adjusted_start_page > adjusted_end_page:
            raise ValueError(f"start_page ({adjusted_start_page}) cannot be greater than end_page ({adjusted_end_page})")

        return adjusted_start_page, adjusted_end_page

    def split(self, input_pdf: str, page_ranges: List[tuple[int, int]], output_dir: Optional[str] = None) -> List[str]:
        """
        Create new PDF files from a list of page ranges in the input PDF.

        Args:
            input_pdf (str): Path to the input PDF file.
            page_ranges (List[tuple[int, int]]): A list of tuples, where each tuple
                                                 contains a start and end page number.
            output_dir (str, optional): Path to the output directory. If not provided,
                                      defaults to the current directory.

        Returns:
            List[str]: A list of paths to the created output PDF files.

        Raises:
            ValueError: If any page range is invalid.
            Exception: If there's an error reading or writing the PDF.
        """
        output_paths = []
        try:
            pdf_path = self._validate_pdf_path(input_pdf)
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                total_pages = len(pdf_reader.pages)

                for start_page, end_page in page_ranges:
                    # Validate and adjust page range
                    start, end = self.validate_page_range(start_page, end_page, total_pages)

                    # Create PDF writer and add selected pages
                    pdf_writer = PyPDF2.PdfWriter()
                    for page_num in range(start - 1, end):
                        pdf_writer.add_page(pdf_reader.pages[page_num])

                    # Generate output filename
                    stem = pdf_path.stem
                    output_filename = f"{stem}_pages_{start}-{end}.pdf"

                    if output_dir:
                        output_path = Path(output_dir) / output_filename
                    else:
                        output_path = Path(output_filename)

                    # Write the output PDF
                    with open(output_path, 'wb') as output_file:
                        pdf_writer.write(output_file)

                    output_paths.append(str(output_path))

            return output_paths
        except PyPDF2.PdfReadError as e:
            raise Exception(f"Error reading PDF file: {e}")
        except Exception as e:
            raise Exception(f"Error processing or writing PDF: {e}")

    def uniform_split(self, input_pdf: str, num_splits: int, output_dir: Optional[str] = None) -> List[str]:
        """
        Split a PDF into a specified number of parts with approximately equal number of pages.

        Args:
            input_pdf (str): Path to the input PDF file.
            num_splits (int): Number of equal parts to split the PDF into.
            output_dir (str, optional): Path to the output directory. If not provided,
                                      defaults to the current directory.

        Returns:
            List[str]: A list of paths to the created output PDF files.

        Raises:
            ValueError: If num_splits is invalid (less than 1) or other validation errors.
            Exception: If there's an error reading or writing the PDF.
        """
        if num_splits < 1:
            raise ValueError(f"num_splits must be at least 1, got {num_splits}")

        try:
            pdf_path = self._validate_pdf_path(input_pdf)
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                total_pages = len(pdf_reader.pages)

            # Calculate pages per split
            pages_per_split = total_pages / num_splits

            # Generate page ranges for uniform splits
            page_ranges = []
            for i in range(num_splits):
                start_page = int(i * pages_per_split) + 1
                end_page = int((i + 1) * pages_per_split)

                # Ensure the last split includes any remaining pages
                if i == num_splits - 1:
                    end_page = total_pages

                page_ranges.append((start_page, end_page))

            # Use the existing split method
            return self.split(input_pdf, page_ranges, output_dir)

        except PyPDF2.PdfReadError as e:
            raise Exception(f"Error reading PDF file: {e}")
        except Exception as e:
            raise Exception(f"Error processing or writing PDF: {e}")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split a PDF file by page ranges.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python split_pdf.py -i input.pdf -r 1 5 10 12"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the input PDF file."
    )
    parser.add_argument(
        "-r", "--ranges",
        nargs='+',
        type=int,
        required=True,
        help="List of page ranges. Must be pairs of start and end pages."
    )
    parser.add_argument(
        "-o", "--output_dir",
        default=None,
        help="Path to the output directory (optional, defaults to current directory)."
    )

    args = parser.parse_args()

    if len(args.ranges) % 2 != 0:
        parser.error("Ranges must be provided in pairs of start and end pages.")

    page_ranges = list(zip(args.ranges[::2], args.ranges[1::2]))

    try:
        splitter = PDFSplitter()
        results = splitter.split(args.input, page_ranges, args.output_dir)
        print("PDFs created successfully:")
        for result in results:
            print(f"- {result}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
