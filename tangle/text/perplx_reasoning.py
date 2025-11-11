"""
Perplexity Reasoning CLI - Step-by-step reasoning about questions.

Uses the reasoning model to provide detailed logical analysis.
"""

import argparse
from pathlib import Path
from text_client import PerplexityTextClient, ReasoningEffort
from shared_utils import success, error, section

DEFAULT_QUESTION = (
    "A farmer has 17 sheep. All but 9 die. How many sheep are left? "
    "Explain your reasoning step-by-step."
)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reason about questions step-by-step",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python perplx_reasoning.py
  python perplx_reasoning.py -q "Why is the sky blue?"
  python perplx_reasoning.py -f questions.txt -o responses.txt
        """
    )

    parser.add_argument("-q", "--question", help="Question to reason about")
    parser.add_argument("-f", "--file", help="File with questions")
    parser.add_argument("-o", "--output", help="Output file")

    args = parser.parse_args()

    try:
        client = PerplexityTextClient()
        success("Client initialized\n")

        # Get questions
        if args.question:
            questions = [args.question]
        elif args.file:
            path = Path(args.file)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {args.file}")
            questions = [line.strip() for line in path.read_text().split('\n') if line.strip()]
        else:
            questions = [DEFAULT_QUESTION]

        if not questions:
            raise ValueError("No questions found")

        # Process questions
        responses = []
        for i, question in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] Reasoning about: {question[:60]}...")
            response = client.reason(question, effort=ReasoningEffort.HIGH)
            responses.append((question, response))

        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                for i, (question, response) in enumerate(responses, 1):
                    f.write(f"[Question {i}]\n{question}\n\n[Reasoning]\n{response}\n\n{'='*60}\n\n")
            success(f"Responses saved to {args.output}")
        else:
            for i, (question, response) in enumerate(responses, 1):
                section(f"REASONING {i}/{len(questions)}", response)

    except ValueError as e:
        error(f"API Error: {e}")
    except FileNotFoundError as e:
        error(f"File Error: {e}")
    except Exception as e:
        error(f"Error: {e}")


if __name__ == "__main__":
    main()
