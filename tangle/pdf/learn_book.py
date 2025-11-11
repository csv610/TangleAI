import sys
import json
from typing import List

from pydantic import BaseModel
from pdf_base import PDFBase


class BookLearning(BaseModel):
    """Schema for book learning analysis results."""
    title: str
    author: str
    genre: str
    summary: str
    key_concepts: List[str]
    main_themes: List[str]
    learning_outcomes: List[str]
    target_audience: str
    chapter_breakdown: List[str]
    practical_applications: List[str]
    key_takeaways: List[str]
    difficulty_level: str
    recommended_prior_knowledge: List[str]
    review_rating: str


class BookLearner(PDFBase):
    """Specialized PDF chat for analyzing and learning from books.

    Returns structured JSON output with BookLearning schema.
    """

    def get_response_schema(self):
        """Return the BookLearning schema for book analysis."""
        return BookLearning

    def get_model_name(self) -> str:
        """Return the model name for book learning analysis."""
        return "sonar-pro"

    def format_output(self, result: str) -> None:
        """Format and display the book analysis result in a structured way."""
        try:
            data = json.loads(result)

            print("\n" + "=" * 80)
            print("📚 BOOK LEARNING ANALYSIS REPORT")
            print("=" * 80 + "\n")

            if "title" in data:
                print(f"📖 TITLE")
                print(f"   {data['title']}\n")

            if "author" in data:
                print(f"✍️  AUTHOR")
                print(f"   {data['author']}\n")

            if "genre" in data:
                print(f"🏷️  GENRE")
                print(f"   {data['genre']}\n")

            if "summary" in data:
                print(f"📄 SUMMARY")
                print(f"   {data['summary']}\n")

            if "key_concepts" in data:
                print(f"🔑 KEY CONCEPTS")
                for concept in data['key_concepts']:
                    print(f"   • {concept}")
                print()

            if "main_themes" in data:
                print(f"🎯 MAIN THEMES")
                for theme in data['main_themes']:
                    print(f"   • {theme}")
                print()

            if "learning_outcomes" in data:
                print(f"🎓 LEARNING OUTCOMES")
                for outcome in data['learning_outcomes']:
                    print(f"   • {outcome}")
                print()

            if "target_audience" in data:
                print(f"👥 TARGET AUDIENCE")
                print(f"   {data['target_audience']}\n")

            if "chapter_breakdown" in data:
                print(f"📑 CHAPTER BREAKDOWN")
                for i, chapter in enumerate(data['chapter_breakdown'], 1):
                    print(f"   {i}. {chapter}")
                print()

            if "practical_applications" in data:
                print(f"💼 PRACTICAL APPLICATIONS")
                for app in data['practical_applications']:
                    print(f"   • {app}")
                print()

            if "key_takeaways" in data:
                print(f"💡 KEY TAKEAWAYS")
                for takeaway in data['key_takeaways']:
                    print(f"   • {takeaway}")
                print()

            if "difficulty_level" in data:
                print(f"⚙️  DIFFICULTY LEVEL")
                print(f"   {data['difficulty_level']}\n")

            if "recommended_prior_knowledge" in data:
                print(f"📚 RECOMMENDED PRIOR KNOWLEDGE")
                for knowledge in data['recommended_prior_knowledge']:
                    print(f"   • {knowledge}")
                print()

            if "review_rating" in data:
                print(f"⭐ REVIEW RATING")
                print(f"   {data['review_rating']}\n")

            print("=" * 80)
        except json.JSONDecodeError:
            print("\n" + "=" * 80)
            print("Book Analysis Result:")
            print("=" * 80)
            print(result)
            print("=" * 80)


# Example usage
if __name__ == "__main__":
    pdf_file = sys.argv[1]
    prompt = "Analyze this book comprehensively and extract key learning insights"

    learner = BookLearner()
    result = learner.generate_text(pdf_file, prompt)
    learner.format_output(result)
