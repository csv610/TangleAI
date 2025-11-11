import sys
import json
from typing import List

from pydantic import BaseModel
from pdf_client import PerplexityPDFClient

class PaperReview(BaseModel):
    """Schema for paper review analysis results."""
    title: str
    author: str
    abstract: str
    key_contribution: List[str]
    hypothesis: List[str]
    claims: List[str]
    verifications: str
    methodology: str
    results: str
    limitations: List[str]
    strengths: List[str]
    weaknesses: List[str]
    overall_rating: str


class PaperReviewer():
    def __init__(self):
        self.client = PerplexityPDFClient()

    def generate_text(self, pdf_file, prompt):
        response = self.client.generate_text(pdf_file, prompt, PaperReview)
        return response

    def format_output(self, result) -> None:
        """Format and display the paper analysis result in a structured way."""
        try:
            # Handle both dict/model and JSON string inputs
            if isinstance(result, dict):
                data = result
            elif isinstance(result, PaperReview):
                data = result.model_dump()
            else:
                data = json.loads(result)

            print("\n" + "=" * 80)
            print("📄 PAPER ANALYSIS REPORT")
            print("=" * 80 + "\n")

            if "title" in data:
                print(f"📌 TITLE")
                print(f"   {data['title']}\n")

            if "author" in data:
                print(f"👤 AUTHOR")
                print(f"   {data['author']}\n")

            if "abstract" in data:
                print(f"📝 ABSTRACT")
                print(f"   {data['abstract']}\n")

            if "key_contribution" in data:
                print(f"💡 KEY CONTRIBUTION")
                print(f"   {data['key_contribution']}\n")

            if "hypothesis" in data:
                print(f"🔮 HYPOTHESIS")
                print(f"   {data['hypothesis']}\n")

            if "claims" in data:
                print(f"📢 CLAIMS")
                print(f"   {data['claims']}\n")

            if "verifications" in data:
                print(f"✅ VERIFICATIONS")
                print(f"   {data['verifications']}\n")

            if "methodology" in data:
                print(f"🔬 METHODOLOGY")
                print(f"   {data['methodology']}\n")

            if "results" in data:
                print(f"📊 RESULTS")
                print(f"   {data['results']}\n")

            if "limitations" in data:
                print(f"⚠️  LIMITATIONS")
                print(f"   {data['limitations']}\n")

            if "strengths" in data:
                print(f"✨ STRENGTHS")
                print(f"   {data['strengths']}\n")

            if "weaknesses" in data:
                print(f"❌ WEAKNESSES")
                print(f"   {data['weaknesses']}\n")

            if "overall_rating" in data:
                print(f"⭐ OVERALL RATING")
                print(f"   {data['overall_rating']}\n")

            print("=" * 80)
        except json.JSONDecodeError:
            print("\n" + "=" * 80)
            print("Analysis Result:")
            print("=" * 80)
            print(result)
            print("=" * 80)


# Example usage
if __name__ == "__main__":
    pdf_file = sys.argv[1]
    prompt = "Please carefully read the PDF and review it comprehensively."

    reviewer = PaperReviewer()
    result = reviewer.generate_text(pdf_file, prompt)
    reviewer.format_output(result)
