"""
Perplexity Research CLI - Deep research with web search and citations.

Investigate topics comprehensively with proper source references.
"""

import argparse
from text_client import PerplexityTextClient, ResearchDepth
from shared_utils import success, error, section

DEFAULT_SOURCES = ["scientific journals", "academic papers", "industry reports"]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Conduct deep research on topics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python perplx_research.py -q "AI ethics"
  python perplx_research.py -q "Climate change" -d COMPREHENSIVE
  python perplx_research.py -q "Quantum computing" -s "Research papers" "News"
        """
    )

    parser.add_argument("-q", "--question", required=True, help="Research topic")
    parser.add_argument(
        "-d", "--depth",
        choices=["BRIEF", "STANDARD", "COMPREHENSIVE"],
        default="STANDARD",
        help="Research depth (default: STANDARD)"
    )
    parser.add_argument("-s", "--sources", nargs="+", help="Sources to focus on")

    args = parser.parse_args()

    try:
        client = PerplexityTextClient()
        success("Client initialized\n")

        # Parse depth
        depth_map = {
            "BRIEF": ResearchDepth.BRIEF,
            "STANDARD": ResearchDepth.STANDARD,
            "COMPREHENSIVE": ResearchDepth.COMPREHENSIVE
        }
        depth = depth_map[args.depth]

        # Get sources
        sources = args.sources or DEFAULT_SOURCES

        # Display parameters
        print(f"Topic: {args.question}")
        print(f"Depth: {args.depth}")
        print(f"Sources: {', '.join(sources)}\n")

        # Conduct research
        response = client.research(args.question, depth=depth, sources=sources)
        section("RESEARCH RESULTS", response)

    except ValueError as e:
        error(f"API Error: {e}")
    except Exception as e:
        error(f"Error: {e}")


if __name__ == "__main__":
    main()
