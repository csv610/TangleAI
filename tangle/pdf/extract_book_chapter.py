#!/usr/bin/env python3
"""
Simple PDF Chapter Extraction Utility.
Extracts chapter information (id, title, start_page, end_page) from PDF files.
"""

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from pypdf import PdfReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("extract_chapters.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ChapterInfo:
    """
    Information about a chapter in a PDF document.

    This dataclass represents a single chapter with its metadata including
    chapter identifier, title, and page range.

    Attributes:
        id (int): Unique chapter identifier, starting from 1.
        title (str): Chapter title or name.
        start_page (int): First page number of the chapter (1-indexed).
        end_page (int): Last page number of the chapter (1-indexed).

    Example:
        >>> chapter = ChapterInfo(id=1, title="Introduction", start_page=1, end_page=10)
        >>> print(f"{chapter.title} (pages {chapter.start_page}-{chapter.end_page})")
        Introduction (pages 1-10)
    """
    id: int
    title: str
    start_page: int
    end_page: int


class BookChaptersExtractor:
    """
    Extract chapter information from PDF documents.

    This class provides functionality to extract chapter metadata from PDF files
    by reading the PDF's table of contents/outline. If no outline is found,
    the entire PDF is treated as a single chapter.

    All operations are logged to 'extract_chapters.log' for debugging and
    tracking purposes.

    Example:
        >>> extractor = BookChaptersExtractor()
        >>> chapters = extractor.extract_chapters("book.pdf", "output.json")
        >>> for ch in chapters:
        ...     print(f"Chapter {ch.id}: {ch.title} (pages {ch.start_page}-{ch.end_page})")
    """

    def __init__(self) -> None:
        """
        Initialize the BookChaptersExtractor.

        Sets up internal state for PDF processing. Note that the PDF file
        is not loaded until extract_chapters() is called.
        """
        self.pdf_file: Optional[str] = None
        self.reader: Optional[PdfReader] = None
        self.total_pages: int = 0
        self.chapters: List[ChapterInfo] = []
        self._chapter_counter: int = 0

    def extract_chapters(self, pdf_file: str, output_json: Optional[str] = None) -> List[ChapterInfo]:
        """
        Extract chapter information from a PDF file.

        Attempts to extract chapters from the PDF's table of contents/outline.
        If no chapters are found in the outline, treats the entire PDF as a single
        chapter with the title "Full Document".

        Args:
            pdf_file (str): Path to the PDF file to extract chapters from.
                Must be an existing file with a valid PDF format.
            output_json (Optional[str]): Path where the extracted chapters should be
                saved as JSON. If None, chapters are only returned in memory without
                being saved to disk. Defaults to None.

        Returns:
            List[ChapterInfo]: List of extracted or generated chapters. Each chapter
                contains an id, title, start_page, and end_page. The list is sorted
                by start_page in ascending order.

        Raises:
            FileNotFoundError: If the specified PDF file does not exist.
            Exception: If the PDF file is corrupted or cannot be read by pypdf.

        Example:
            >>> extractor = BookChaptersExtractor()
            >>> # Extract chapters without saving
            >>> chapters = extractor.extract_chapters("book.pdf")
            >>> print(f"Found {len(chapters)} chapters")
            Found 12 chapters

            >>> # Extract chapters and save to JSON
            >>> chapters = extractor.extract_chapters("book.pdf", "chapters.json")
            >>> for ch in chapters:
            ...     print(f"{ch.id}. {ch.title}")

        Note:
            - If no outline exists, the entire PDF becomes one chapter titled "Full Document"
            - All operations are logged to extract_chapters.log
            - The class maintains state between calls; extract_chapters() can be called
              multiple times with different PDFs
        """
        # Check if PDF file exists
        if not os.path.exists(pdf_file):
            logger.error(f"PDF file not found: {pdf_file}")
            raise FileNotFoundError(f"PDF file not found: {pdf_file}")

        self.pdf_file = pdf_file
        self.reader = PdfReader(pdf_file)
        self.total_pages = len(self.reader.pages)

        logger.info(f"Extracting chapters from: {self.pdf_file}")
        logger.info(f"Total pages: {self.total_pages}")

        # Try to extract from PDF outline/TOC, then text-based TOC, fallback to treating entire PDF as one chapter
        chapters = self._extract_from_outline() or self._extract_from_text_toc() or self._create_single_chapter()

        # Calculate end pages and sort by start page
        chapters = self._add_end_pages(chapters)
        chapters = sorted(chapters, key=lambda x: x["start_page"])

        # Convert to ChapterInfo objects
        self.chapters = [
            ChapterInfo(
                id=ch["id"],
                title=ch["title"],
                start_page=ch["start_page"],
                end_page=ch["end_page"],
            )
            for ch in chapters
        ]

        logger.info(f"Found {len(self.chapters)} chapters")

        # Generate default output filename if not provided
        if output_json is None:
            output_json = os.path.splitext(pdf_file)[0] + "_chapters.json"

        # Export to JSON
        self._export_to_json(output_json)

        return self.chapters

    def _export_to_json(self, output_file: str) -> None:
        """
        Export extracted chapters to a JSON file.

        Saves the chapters metadata along with PDF information to a JSON file.
        The JSON structure includes document metadata and a chapters array.

        Args:
            output_file (str): Path where the JSON file should be saved.
                If the file exists, it will be overwritten.

        Returns:
            None

        Raises:
            IOError: If the file cannot be written (permission denied, invalid path, etc).

        Example:
            >>> extractor = BookChaptersExtractor()
            >>> chapters = extractor.extract_chapters("book.pdf")
            >>> extractor._export_to_json("output.json")

        JSON Structure:
            {
                "pdf_file": "book.pdf",
                "total_pages": 300,
                "chapters": [
                    {
                        "id": 1,
                        "title": "Chapter 1",
                        "start_page": 1,
                        "end_page": 25
                    },
                    ...
                ]
            }

        Note:
            - This is a private method, typically called automatically by extract_chapters()
            - The output JSON uses 2-space indentation for readability
            - All chapter information is preserved in the JSON output
        """
        data = {
            "pdf_file": self.pdf_file,
            "total_pages": self.total_pages,
            "chapters": [asdict(ch) for ch in self.chapters],
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported chapters to: {output_file}")

    # ========== Private Methods ==========

    def _extract_from_outline(self) -> List[Dict]:
        """
        Extract chapters from PDF table of contents/outline.

        Attempts to parse the PDF's document outline (also called bookmarks or TOC).
        Returns an empty list if no outline exists or if an error occurs during parsing.

        Returns:
            List[Dict]: List of chapters extracted from the outline. Each chapter dict
                contains 'id', 'title', and 'start_page' keys. Returns empty list if
                no outline found or on parsing error.

        Note:
            - This is a private method called internally by extract_chapters()
            - Resets the chapter counter before parsing to ensure unique IDs
            - Logs warnings and errors for debugging purposes
        """
        logger.info("Trying PDF outline...")

        if not self.reader.outline:
            logger.warning("No outline found in PDF")
            return []

        try:
            self._chapter_counter = 0
            chapters = self._parse_outline_items(self.reader.outline)
            if chapters:
                logger.info(f"Found {len(chapters)} chapters in outline")
            return chapters
        except Exception as e:
            logger.error(f"Error parsing outline: {e}")
            return []

    def _extract_from_text_toc(self) -> List[Dict]:
        """
        Extract chapters from text-based table of contents in early PDF pages.

        Scans the first 15 pages of the PDF for a "TABLE OF CONTENTS" section
        and extracts chapter information from the text. Then finds actual chapter
        header locations in the PDF to get correct page numbers.

        Returns:
            List[Dict]: List of chapters extracted from text TOC with actual page numbers.
                Each chapter dict contains 'id', 'title', and 'start_page' keys.
                Returns empty list if no TOC found or on parsing error.

        Note:
            - This is a fallback method when no embedded outline exists
            - Only processes first 15 pages to find TOC
            - Uses actual chapter headers to determine page numbers (not TOC page numbers)
            - Logs info about TOC extraction attempts
        """
        logger.info("Trying text-based table of contents...")

        try:
            # Search first 15 pages for TOC
            toc_start = None
            toc_text = ""

            for page_num in range(min(15, len(self.reader.pages))):
                text = self.reader.pages[page_num].extract_text()
                if "TABLE OF CONTENTS" in text.upper() or "CONTENTS" in text.upper():
                    toc_start = page_num
                    toc_text += text
                    # Get next 1-2 pages as well for complete TOC
                    for next_page in range(page_num + 1, min(page_num + 3, len(self.reader.pages))):
                        toc_text += "\n" + self.reader.pages[next_page].extract_text()
                    break

            if not toc_text:
                logger.warning("No text-based TOC found in first 15 pages")
                return []

            chapters = self._parse_text_toc(toc_text)
            if chapters:
                # Now find actual chapter header locations for correct page numbers
                chapters = self._find_actual_chapter_pages(chapters)
                logger.info(f"Found {len(chapters)} chapters in text-based TOC")
            return chapters

        except Exception as e:
            logger.error(f"Error parsing text-based TOC: {e}")
            return []

    def _find_actual_chapter_pages(self, chapters: List[Dict]) -> List[Dict]:
        """
        Find actual chapter starting pages by searching for chapter headers in PDF.

        Scans through the PDF to find "CHAPTER N" headers and updates the
        start_page for each chapter with the actual PDF page where the header appears.

        Args:
            chapters (List[Dict]): List of chapters from TOC with preliminary page numbers.

        Returns:
            List[Dict]: Same chapters list with start_page updated to actual header locations.

        Note:
            - Updates chapters in-place
            - Only updates chapters where a header is found
            - Scans from page 10 onwards (skipping front matter)
        """
        chapter_headers = {}

        # Search PDF for actual chapter headers
        for page_num in range(10, len(self.reader.pages)):
            text = self.reader.pages[page_num].extract_text()

            # Look for chapter headers
            match = re.search(r"^CHAPTER\s+(\d+)", text, re.MULTILINE | re.IGNORECASE)
            if match:
                ch_num = int(match.group(1))
                chapter_headers[ch_num] = page_num + 1  # 1-indexed

        # Update chapters with actual page numbers
        for chapter in chapters:
            ch_id = chapter["id"]
            if ch_id in chapter_headers:
                chapter["start_page"] = chapter_headers[ch_id]
                logger.debug(f"Updated Chapter {ch_id} to start at PDF page {chapter_headers[ch_id]}")

        return chapters

    def _parse_text_toc(self, toc_text: str) -> List[Dict]:
        """
        Parse chapter information from text-based TOC.

        Extracts chapter entries from TOC, handling multi-line titles.
        Looks for patterns like:
        - "page_number  Chapter N: Title"
        - Handles titles that span multiple lines

        Args:
            toc_text (str): The raw text extracted from TOC pages.

        Returns:
            List[Dict]: List of parsed chapters with 'id', 'title', and 'start_page'.

        Note:
            - Only extracts lines that contain "Chapter" keyword
            - Handles multi-line titles by looking ahead
            - Skips sub-items (tests, sections) that don't have "Chapter" keyword
        """
        chapters = []
        self._chapter_counter = 0

        # Split by lines
        lines = toc_text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Look for lines with "Chapter" keyword
            if line and "chapter" in line.lower():
                # Pattern: "page_number  Chapter N: Title" or multi-line
                match = re.match(r"^(\d+)\s+Chapter\s+(\d+)[:\s]+(.*?)\s*$", line, re.IGNORECASE)

                if match:
                    try:
                        page_num = int(match.group(1))
                        chapter_num = int(match.group(2))
                        title = match.group(3).strip()

                        # If title is incomplete (ends abruptly), get next line
                        if not title or (i + 1 < len(lines) and not lines[i + 1].strip()[0].isdigit()):
                            # Next line might be continuation of title
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                # If next line doesn't start with a number, it's part of the title
                                if next_line and not re.match(r"^\d+\s+", next_line):
                                    title += " " + next_line
                                    i += 1

                        # Clean up extra spaces
                        title = re.sub(r'\s+', ' ', title)

                        if title:
                            self._chapter_counter += 1
                            chapters.append({
                                "id": chapter_num,
                                "title": self._clean_chapter_title(title),
                                "start_page": page_num,
                            })
                            logger.debug(f"Found chapter: {chapter_num} - {self._clean_chapter_title(title)} (p. {page_num})")
                    except (ValueError, IndexError):
                        pass

            i += 1

        return chapters

    def _is_front_matter(self, title: str) -> bool:
        """
        Check if a title belongs to front matter sections.

        Filters out common front matter items like preface, acknowledgements,
        table of contents, etc., to include only actual chapters.

        Args:
            title (str): The outline item title to check.

        Returns:
            bool: True if the title is front matter, False if it's a chapter.

        Note:
            - Case-insensitive matching
            - Checks for exact matches and common variations
        """
        front_matter_keywords = {
            "preface",
            "foreword",
            "introduction",
            "acknowledgement",
            "acknowledgments",
            "contents",
            "table of contents",
            "toc",
            "prologue",
            "questions",
            "answers and explanations",
            "answers",
            "explanations",
        }

        title_lower = title.lower().strip()
        return title_lower in front_matter_keywords

    def _is_back_matter(self, title: str) -> bool:
        """
        Check if a title belongs to back matter sections.

        Filters out common back matter items like index, references, appendix,
        bibliography, etc., to exclude from chapter content.

        Args:
            title (str): The outline item title to check.

        Returns:
            bool: True if the title is back matter, False if it's chapter content.

        Note:
            - Case-insensitive matching
            - Checks for exact matches and common variations
        """
        back_matter_keywords = {
            "index",
            "bibliography",
            "references",
            "appendix",
            "appendices",
            "about the author",
            "author bio",
            "author biography",
            "copyright",
            "disclaimer",
            "colophon",
            "glossary",
            "notes",
            "endnotes",
            "further reading",
        }

        title_lower = title.lower().strip()
        return title_lower in back_matter_keywords

    def _extract_chapter_number(self, title: str) -> Optional[int]:
        """
        Extract chapter number from the title.

        Attempts to parse chapter numbers from titles like:
        - "Chapter 1", "Chapter 1: Title"
        - "Ch. 5", "Ch 5"
        - "1.", "1 - Title", "1 Skin", "2 Skin"

        Args:
            title (str): The chapter title to parse.

        Returns:
            Optional[int]: The extracted chapter number if found, None otherwise.

        Note:
            - Uses regex to find the first number in the title
            - Case-insensitive for "chapter" keyword
        """
        title_stripped = title.strip()

        # Try to match "Chapter N", "Ch. N", "Ch N" patterns
        match = re.match(r"(?:chapter|ch\.?)\s+(\d+)", title_stripped, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Try to match leading number: "1.", "1 -", "1:"
        match = re.match(r"^(\d+)[\.\s\-:]", title_stripped)
        if match:
            return int(match.group(1))

        return None

    def _clean_chapter_title(self, title: str) -> str:
        """
        Clean chapter title by removing leading chapter numbers and identifiers.

        Removes patterns like:
        - "1. Title" -> "Title"
        - "1 - Title" -> "Title"
        - "Chapter 1: Title" -> "Title"
        - "Ch. 1 Title" -> "Title"
        - "1 Title" -> "Title"

        Args:
            title (str): The raw chapter title to clean.

        Returns:
            str: The cleaned title with leading chapter identifiers removed.

        Note:
            - Case-insensitive for "chapter"/"ch" keywords
            - Preserves the actual chapter content after the identifier
            - Returns original title if no pattern matches
        """
        title_stripped = title.strip()

        # Pattern 1: "Chapter N: Title" or "Ch. N: Title" or "Ch N: Title"
        match = re.match(r"(?:chapter|ch\.?)\s+\d+[:\s]+(.+)", title_stripped, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Pattern 2: "N. Title", "N - Title", "N: Title"
        match = re.match(r"^\d+[\.\s\-:]+(.+)$", title_stripped)
        if match:
            return match.group(1).strip()

        # Pattern 3: "N Title" (number followed by space and text)
        match = re.match(r"^\d+\s+(.+)$", title_stripped)
        if match:
            return match.group(1).strip()

        return title_stripped

    def _parse_outline_items(self, items: list, depth: int = 0) -> List[Dict]:
        """
        Parse top-level outline items to extract chapter information.

        Extracts title and page number from each top-level outline item.
        Filters out front matter sections (preface, contents, acknowledgements, etc.)
        and back matter sections. Only extracts items with explicit chapter numbers
        from titles (e.g., "Chapter 5" or "5 Title").

        Args:
            items (list): List of outline items to parse. Only top-level items
                (not nested lists) are processed.
            depth (int): Current recursion depth. Only top-level items (depth=0)
                are extracted.

        Returns:
            List[Dict]: Extracted chapters with 'id', 'title', and 'start_page' keys.
                Skips items without chapter numbers, front matter, and back matter.

        Note:
            - This method only processes top-level outline items
            - Does NOT recursively extract nested items (sub-sections, appendices, etc.)
            - Chapter ID is extracted from title (e.g., "Chapter 5" -> id=5)
            - Skips items that don't have explicit chapter numbers
            - Silently skips items that cannot be parsed
        """
        chapters = []

        for item in items:
            try:
                # Skip nested lists - only process top-level items
                # This avoids extracting appendix sub-sections or other nested content
                if isinstance(item, list):
                    continue

                # Extract title and page number from outline item
                title = self._get_outline_item_info(item)
                if not title:
                    continue

                # Skip front matter sections
                if self._is_front_matter(title):
                    logger.debug(f"Skipping front matter: {title}")
                    continue

                # Skip back matter sections
                if self._is_back_matter(title):
                    logger.debug(f"Skipping back matter: {title}")
                    continue

                page_num = self._get_outline_page_num(item)
                if page_num is None:
                    continue

                # Extract chapter number from title
                chapter_num = self._extract_chapter_number(title)

                # Only extract items that have explicit chapter numbers
                # Items without numbers (like appendix sub-sections) are skipped
                if chapter_num is None:
                    continue

                # Skip single-letter entries (dictionary entries, etc.)
                if len(title.strip()) == 1:
                    continue

                # Update counter to avoid duplicates when using extracted numbers
                self._chapter_counter = max(self._chapter_counter, chapter_num)

                chapters.append({
                    "id": chapter_num,
                    "title": self._clean_chapter_title(title),
                    "start_page": page_num,
                })
            except Exception:
                continue

        return chapters

    def _get_outline_item_info(self, item) -> Optional[str]:
        """
        Extract title from an outline item.

        Handles different types of outline items (dict, objects with get method).
        Safely extracts the '/Title' field which is the PDF standard for outline titles.

        Args:
            item: An outline item object (could be dict, pypdf object, etc).

        Returns:
            Optional[str]: The title string if found, empty string if not found,
                None if the item type is unsupported or an error occurs.

        Note:
            - This is a private method used internally during outline parsing
            - Returns empty string rather than None when title field doesn't exist
            - Silently handles exceptions for robustness
        """
        try:
            if isinstance(item, dict):
                return item.get("/Title", "")
            if hasattr(item, 'get'):
                return item.get("/Title", "")
            return None
        except (AttributeError, TypeError):
            return None

    def _get_outline_page_num(self, item) -> Optional[int]:
        """
        Extract page number from an outline item.

        Uses pypdf's get_destination_page_number() to find the page number
        that the outline item points to. Converts from 0-indexed to 1-indexed.

        Args:
            item: An outline item object from the PDF's document outline.

        Returns:
            Optional[int]: The page number (1-indexed) if extraction succeeds,
                None if the item has no valid page destination or an error occurs.

        Note:
            - This is a private method used internally during outline parsing
            - pypdf returns 0-indexed page numbers, this method converts to 1-indexed
            - Returns None rather than raising exceptions for robustness
        """
        try:
            return self.reader.get_destination_page_number(item) + 1
        except Exception:
            return None

    def _create_single_chapter(self) -> List[Dict]:
        """
        Create a single chapter representing the entire PDF document.

        This is used as a fallback when the PDF has no outline/table of contents.
        The generated chapter spans the entire document.

        Returns:
            List[Dict]: A list containing a single chapter dict with 'id', 'title',
                and 'start_page' keys. The 'end_page' is added later by _add_end_pages().

        Note:
            - This is a private method called automatically when no outline is found
            - The returned chapter dict is incomplete; _add_end_pages() must be called
              afterward to add the 'end_page' field
            - The chapter is always titled "Full Document"
        """
        logger.info("No chapters found, treating entire PDF as one chapter")
        return [{
            "id": 1,
            "title": "Full Document",
            "start_page": 1,
        }]

    def _add_end_pages(self, chapters: List[Dict]) -> List[Dict]:
        """
        Calculate and add end_page field to each chapter.

        For each chapter, the end_page is set to the page before the next chapter starts.
        The last chapter's end_page is set to the page before back matter begins.
        Back matter sections (Index, References, Appendix, etc.) are excluded from
        the last chapter content.

        Args:
            chapters (List[Dict]): List of chapter dicts with 'id', 'title', and
                'start_page' keys. This list is modified in-place.

        Returns:
            List[Dict]: The same chapter list with 'end_page' field added to each chapter.

        Example:
            >>> chapters = [
            ...     {"id": 1, "title": "Ch 1", "start_page": 1},
            ...     {"id": 2, "title": "Ch 2", "start_page": 30},
            ... ]
            >>> self._add_end_pages(chapters)
            >>> chapters[0]
            {'id': 1, 'title': 'Ch 1', 'start_page': 1, 'end_page': 29}
            >>> chapters[1]
            {'id': 2, 'title': 'Ch 2', 'start_page': 30, 'end_page': <last_chapter_page>}

        Note:
            - This is a private method that modifies the input list in-place
            - Must be called after extracting chapters but before converting to ChapterInfo
            - Assumes chapters are passed in order by start_page (though not enforced)
            - The last chapter's end_page excludes back matter sections
        """
        for i, chapter in enumerate(chapters):
            if i + 1 < len(chapters):
                chapter["end_page"] = chapters[i + 1]["start_page"] - 1
            else:
                # For the last chapter, find where back matter starts
                last_chapter_end = self._find_back_matter_start()
                chapter["end_page"] = last_chapter_end

        return chapters

    def _find_back_matter_start(self) -> int:
        """
        Find the page where back matter starts in the PDF.

        Scans the PDF's outline for back matter items (Index, References, Appendix, etc.)
        at the top level only and returns the page number before the first back matter section.
        If no back matter is found, returns the total number of pages.

        Returns:
            int: The page number (1-indexed) where back matter starts. If no back matter
                is found, returns total_pages.

        Note:
            - This is a private method used to determine the last chapter's end_page
            - Looks for back matter in the PDF outline (top-level items only)
            - Returns total_pages if no back matter sections are found
            - Only considers top-level outline items to avoid chapter references
        """
        back_matter_start = self.total_pages

        try:
            # Check if PDF has outline
            if not self.reader.outline:
                return back_matter_start

            # Search ONLY top-level outline items for back matter
            # This avoids confusing chapter references with document back matter
            for item in self.reader.outline:
                try:
                    # Skip nested items (lists)
                    if isinstance(item, list):
                        continue

                    title = self._get_outline_item_info(item)
                    if title and self._is_back_matter(title):
                        page_num = self._get_outline_page_num(item)
                        if page_num is not None:
                            back_matter_start = min(back_matter_start, page_num)
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Error finding back matter start: {e}")

        # Return the page before back matter starts (or total_pages if none found)
        if back_matter_start == self.total_pages:
            # No back matter found, return total pages
            return self.total_pages
        else:
            # Back matter found, return the page before it starts
            return max(1, back_matter_start - 1)

def main():
    """
    Command-line interface for the PDF chapter extraction utility.

    Parses command-line arguments and runs the chapter extraction process.
    Supports optional JSON export of the extracted chapters.

    Command-line Arguments:
        pdf_file (str): Path to the PDF file to process. Required.
        -o, --output (str): Optional path to save the extracted chapters as JSON.

    Examples:
        Extract chapters without saving:
            $ python extract_book_chapter.py book.pdf

        Extract chapters and save to JSON:
            $ python extract_book_chapter.py book.pdf -o chapters.json
            $ python extract_book_chapter.py book.pdf --output chapters.json

    Returns:
        BookChaptersExtractor: The extractor instance with extracted chapters.

    Note:
        - All operations are logged to extract_chapters.log
        - Exits with code 1 if the PDF file is not found
    """
    parser = argparse.ArgumentParser(
        description="Extract chapter information from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python extract_book_chapter.py book.pdf
  python extract_book_chapter.py book.pdf -o chapters.json
  python extract_book_chapter.py book.pdf --output chapters.json
        """,
    )

    parser.add_argument(
        "-i", "--pdf_file",
        help="Path to the PDF file to extract chapters from",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_json",
        default=None,
        help="Optional path to save the extracted chapters as JSON",
    )

    args = parser.parse_args()

    # Extract chapters (and optionally export to JSON)
    extractor = BookChaptersExtractor()
    chapters = extractor.extract_chapters(args.pdf_file, args.output_json)

    return extractor


if __name__ == "__main__":
    main()
