import sys
import json
from typing import List, Dict

from pydantic import BaseModel
from pdf_base import PDFBase


class ChapterAnalysis(BaseModel):
    """Schema for individual chapter analysis."""
    chapter_number: int
    chapter_title: str
    summary: str
    key_concepts: List[str]
    main_topics: List[str]
    learning_points: List[str]
    practical_applications: List[str]
    questions_to_consider: List[str]
    connections_to_other_chapters: List[str]


class BookChapterLearning(BaseModel):
    """Schema for complete book chapter-by-chapter analysis results."""
    book_title: str
    book_author: str
    total_chapters: int
    book_overview: str
    chapters: List[ChapterAnalysis]
    overall_learning_path: str
    prerequisites: List[str]
    key_skills_developed: List[str]


class BookChapterLearner(PDFBase):
    """Specialized PDF chat for analyzing books chapter by chapter.

    Returns structured JSON output with detailed chapter-by-chapter analysis.
    """

    def get_response_schema(self):
        """Return the BookChapterLearning schema for chapter analysis."""
        return BookChapterLearning

    def get_model_name(self) -> str:
        """Return the model name for book chapter learning analysis."""
        return "sonar-pro"

    def format_output(self, result: str) -> None:
        """Format and display the chapter-by-chapter analysis in a structured way."""
        try:
            data = json.loads(result)

            print("\n" + "=" * 100)
            print("📚 CHAPTER-BY-CHAPTER BOOK LEARNING ANALYSIS")
            print("=" * 100 + "\n")

            # Book Header Information
            if "book_title" in data:
                print(f"📖 BOOK TITLE")
                print(f"   {data['book_title']}\n")

            if "book_author" in data:
                print(f"✍️  AUTHOR")
                print(f"   {data['book_author']}\n")

            if "total_chapters" in data:
                print(f"📑 TOTAL CHAPTERS")
                print(f"   {data['total_chapters']}\n")

            if "book_overview" in data:
                print(f"📄 BOOK OVERVIEW")
                print(f"   {data['book_overview']}\n")

            if "prerequisites" in data and data['prerequisites']:
                print(f"📚 PREREQUISITES")
                for prereq in data['prerequisites']:
                    print(f"   • {prereq}")
                print()

            if "overall_learning_path" in data:
                print(f"🛤️  OVERALL LEARNING PATH")
                print(f"   {data['overall_learning_path']}\n")

            if "key_skills_developed" in data and data['key_skills_developed']:
                print(f"🎯 KEY SKILLS DEVELOPED")
                for skill in data['key_skills_developed']:
                    print(f"   • {skill}")
                print()

            # Chapter-by-Chapter Analysis
            if "chapters" in data and data['chapters']:
                print("=" * 100)
                print("DETAILED CHAPTER ANALYSIS")
                print("=" * 100 + "\n")

                for chapter in data['chapters']:
                    self._format_chapter(chapter)

            print("=" * 100)

        except json.JSONDecodeError:
            print("\n" + "=" * 100)
            print("Book Chapter Analysis Result:")
            print("=" * 100)
            print(result)
            print("=" * 100)

    def _format_chapter(self, chapter: Dict) -> None:
        """Format individual chapter information."""
        if "chapter_number" in chapter and "chapter_title" in chapter:
            print(f"\n📌 CHAPTER {chapter['chapter_number']}: {chapter['chapter_title']}")
            print("-" * 100)

        if "summary" in chapter:
            print(f"\n📝 SUMMARY")
            print(f"   {chapter['summary']}\n")

        if "key_concepts" in chapter and chapter['key_concepts']:
            print(f"🔑 KEY CONCEPTS")
            for concept in chapter['key_concepts']:
                print(f"   • {concept}")
            print()

        if "main_topics" in chapter and chapter['main_topics']:
            print(f"🎯 MAIN TOPICS")
            for topic in chapter['main_topics']:
                print(f"   • {topic}")
            print()

        if "learning_points" in chapter and chapter['learning_points']:
            print(f"💡 LEARNING POINTS")
            for point in chapter['learning_points']:
                print(f"   • {point}")
            print()

        if "practical_applications" in chapter and chapter['practical_applications']:
            print(f"💼 PRACTICAL APPLICATIONS")
            for app in chapter['practical_applications']:
                print(f"   • {app}")
            print()

        if "questions_to_consider" in chapter and chapter['questions_to_consider']:
            print(f"❓ QUESTIONS TO CONSIDER")
            for i, question in enumerate(chapter['questions_to_consider'], 1):
                print(f"   {i}. {question}")
            print()

        if "connections_to_other_chapters" in chapter and chapter['connections_to_other_chapters']:
            print(f"🔗 CONNECTIONS TO OTHER CHAPTERS")
            for connection in chapter['connections_to_other_chapters']:
                print(f"   • {connection}")
            print()


# Example usage
if __name__ == "__main__":
    pdf_file = sys.argv[1]
    prompt = """Analyze this book chapter by chapter. For each chapter, provide:
    1. Chapter number and title
    2. Summary of the chapter
    3. Key concepts introduced
    4. Main topics covered
    5. Key learning points
    6. Practical applications
    7. Questions to consider for deeper understanding
    8. Connections to other chapters or concepts

    Also provide an overall book overview, prerequisites, and key skills developed throughout the book."""

    learner = BookChapterLearner()
    result = learner.generate_text(pdf_file, prompt)
    learner.format_output(result)
