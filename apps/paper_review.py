import sys
import os
import json
from typing import List

# Add tangle directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tangle'))

from pydantic import BaseModel
from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput


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


class PaperReviewer:
    """Reviews academic papers using Perplexity AI with PDF analysis."""

    def __init__(self, config: ModelConfig = None):
        """
        Initialize the paper reviewer.

        Args:
            config: Optional ModelConfig for API calls. If not provided, uses sensible defaults.

        Raises:
            ValueError: If PERPLEXITY_API_KEY environment variable is not set.
        """
        self.config = config or ModelConfig(
            model="sonar-pro",
            max_tokens=4096,
            temperature=0.7,
            top_p=0.9,
            stream=False,
            search_mode="web"
        )
        self.client = PerplexityClient(self.config)

    def generate_text(self, pdf_file: str, prompt: str) -> PaperReview:
        """
        Generate a comprehensive paper review analysis from a PDF file.

        Args:
            pdf_file: Path to the PDF file to analyze
            prompt: Custom prompt for the analysis (optional, overrides default)

        Returns:
            PaperReview: Structured analysis of the paper

        Raises:
            FileNotFoundError: If PDF file does not exist
            ValueError: If analysis fails
        """
        if not os.path.exists(pdf_file):
            raise FileNotFoundError(f"PDF file not found: {pdf_file}")

        print(f"Analyzing paper: {pdf_file}")

        # Create model input with PDF and structured output
        model_input = ModelInput(
            user_prompt=prompt,
            pdf_path=pdf_file,
            response_model=PaperReview
        )

        try:
            # Call Perplexity API with PDF and structured output
            response = self.client.generate_content(model_input, self.config)

            # Validate and parse the response
            paper_review = PaperReview.model_validate_json(
                response.choices[0].message.content
            )

            print(f"  ✓ Successfully analyzed paper: {paper_review.title}")
            return paper_review

        except ValueError as e:
            raise ValueError(f"Failed to analyze paper: {str(e)}")
        except Exception as e:
            raise Exception(f"Error during paper analysis: {str(e)}")

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
    if len(sys.argv) < 2:
        print("Usage: python paper_review.py <pdf_file> [custom_prompt]")
        print("Example: python paper_review.py research_paper.pdf")
        sys.exit(1)

    pdf_file = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Please carefully read the PDF and review it comprehensively. Provide a detailed academic analysis covering all the required fields."

    try:
        reviewer = PaperReviewer()
        result = reviewer.generate_text(pdf_file, prompt)
        reviewer.format_output(result)

        # Save to JSON
        output_file = f"{os.path.splitext(pdf_file)[0]}_review.json"
        with open(output_file, 'w') as f:
            json.dump(result.model_dump(mode='json'), f, indent=2)

        print(f"\nFull review saved to: {output_file}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
