"""
Perplexity Query CLI - Simple, fast queries.

Query single or batch prompts from the command line.
"""

import argparse
import sys
from pathlib import Path
from text_client import PerplexityTextClient
from shared_utils import success, error, section, SEPARATOR


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query Perplexity AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python perplx_query.py -q "What is AI?"
  python perplx_query.py -f questions.txt
  python perplx_query.py -f questions.txt -o results.txt
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-q", "--query", help="Single query")
    group.add_argument("-f", "--file", help="File with queries (one per line)")
    parser.add_argument("-o", "--output", help="Output file")

    args = parser.parse_args()

    try:
        client = PerplexityTextClient()
        success("Client initialized")

        if args.query:
            _query_single(client, args.query)
        else:
            _query_file(client, args.file, args.output)

    except ValueError as e:
        error(f"API Error: {e}")
    except FileNotFoundError as e:
        error(f"File Error: {e}")
    except Exception as e:
        error(f"Error: {e}")


def _query_single(client: PerplexityTextClient, query: str) -> None:
    """Execute a single query."""
    print(f"\nQuerying: {query}")
    response = client.query(query)
    section("RESPONSE", response)


def _query_file(client: PerplexityTextClient, file_path: str, output_path: str = None) -> None:
    """Execute queries from a file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load queries
    queries = [line.strip() for line in path.read_text().split('\n') if line.strip()]

    if not queries:
        raise ValueError("No queries found in file")

    success(f"Loaded {len(queries)} queries from {file_path}\n")

    # Process queries
    responses = []
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {query}")
        response = client.query(query)
        responses.append((query, response))

    # Save results
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = path.parent / f"{path.stem}_responses.txt"

    with open(out_file, 'w') as f:
        for i, (query, response) in enumerate(responses, 1):
            f.write(f"[Question {i}]\n{query}\n\n[Response]\n{response}\n\n{SEPARATOR}\n\n")

    success(f"Responses saved to {out_file}")


if __name__ == "__main__":
    main()
