#!/usr/bin/env python3
"""
Hilbert's 23 Problems Reference Guide
Dynamically fetches and documents all 23 problems proposed by David Hilbert in 1900,
using Perplexity API for current and comprehensive information
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent / "tangle"))

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput
from logging_utils import setup_logging

logger = setup_logging("hilbert_problems.log")


class ProblemStatus(str, Enum):
    """Status of Hilbert problems."""
    SOLVED = "solved"
    UNSOLVED = "unsolved"
    PARTIALLY_SOLVED = "partially_solved"


class HilbertProblem(BaseModel):
    """Structured data for a Hilbert problem."""
    number: int = Field(description="Problem number (1-23)")
    title: str = Field(description="Title of the problem")
    description: str = Field(description="Mathematical description of the problem")
    status: ProblemStatus = Field(description="Current status of the problem")
    solved_by: Optional[str] = Field(description="Mathematician(s) who solved it")
    solution_year: Optional[int] = Field(description="Year the problem was solved")
    solution_method: str = Field(description="Detailed explanation of the solution method")
    related_fields: List[str] = Field(description="Related mathematical fields")
    notes: str = Field(description="Additional notes and implications")


class HilbertProblemsGuide:
    """Reference guide for Hilbert's 23 problems using Perplexity API."""

    def __init__(self, config: Optional[ModelConfig] = None):
        """
        Initialize the guide with API client and cache.

        Args:
            config: Optional ModelConfig. If not provided, uses sensible defaults.
        """
        self.config = config or ModelConfig(model="sonar")
        self.client = PerplexityClient()
        self.cache: Dict[int, Optional[HilbertProblem]] = {}

    @staticmethod
    def _validate_problem_number(problem_number: int) -> None:
        """
        Validate that problem number is between 1 and 23.

        Args:
            problem_number: Problem number to validate

        Raises:
            ValueError: If problem_number is not between 1 and 23
        """
        if problem_number < 1 or problem_number > 23:
            raise ValueError(f"Problem number must be between 1 and 23, got {problem_number}")

    def get_problem(self, problem_number: int) -> Optional[HilbertProblem]:
        """
        Fetch a specific Hilbert problem from the API.

        Args:
            problem_number: Problem number (1-23)

        Returns:
            HilbertProblem instance or None if fetch fails

        Raises:
            ValueError: If problem_number is not between 1 and 23
        """
        self._validate_problem_number(problem_number)

        if problem_number in self.cache:
            return self.cache[problem_number]

        try:
            logger.info(f"Fetching Hilbert problem {problem_number} from API")

            prompt = f"""
            Provide comprehensive information about Hilbert's Problem #{problem_number}.
            Include:
            - Title
            - Mathematical description
            - Current status (solved/unsolved/partially solved)
            - Who solved it and when
            - Detailed solution method/explanation
            - Related mathematical fields (as a list)
            - Important notes

            Return the response with these exact field names: number, title, description, status,
            solved_by, solution_year, solution_method, related_fields, notes
            """

            model_input = ModelInput(
                user_prompt=prompt,
                response_model=HilbertProblem
            )

            response = self.client.generate_content(model_input, self.config)

            if response.json:
                problem = response.json
                # Ensure number field is set correctly
                if problem.number != problem_number:
                    problem.number = problem_number
                self.cache[problem_number] = problem
                logger.info(f"Successfully fetched problem {problem_number}: {problem.title}")
                return problem
            else:
                logger.error(f"No structured output received for problem {problem_number}")
                return None

        except Exception as e:
            logger.error(f"Error fetching problem {problem_number}: {str(e)}")
            return None

    def get_all_problems(self) -> Dict[int, HilbertProblem]:
        """
        Fetch all 23 Hilbert problems from the API.

        Returns:
            Dictionary mapping problem numbers to HilbertProblem instances
        """
        all_problems = {}
        for problem_num in tqdm(range(1, 24), desc="Fetching Hilbert Problems"):
            problem = self.get_problem(problem_num)
            if problem:
                all_problems[problem_num] = problem

        logger.info(f"Fetched {len(all_problems)} Hilbert problems")
        return all_problems

    @staticmethod
    def display_problem(problem: Optional[HilbertProblem]) -> None:
        """
        Display a Hilbert problem in formatted terminal output.

        Args:
            problem: HilbertProblem instance to display
        """
        if not problem:
            print("\n❌ Problem not found")
            return

        status_emoji = {
            ProblemStatus.SOLVED: "✅",
            ProblemStatus.UNSOLVED: "❓",
            ProblemStatus.PARTIALLY_SOLVED: "⚠️"
        }

        print("\n" + "=" * 90)
        print(f"Problem {problem.number}: {problem.title} {status_emoji[problem.status]}")
        print("=" * 90)

        print(f"\n📝 DESCRIPTION:")
        print("-" * 90)
        print(problem.description)

        print(f"\n📊 STATUS: {problem.status.value.upper()}")
        if problem.solved_by:
            print(f"   Solved by: {problem.solved_by}")
        if problem.solution_year:
            print(f"   Year: {problem.solution_year}")

        print(f"\n🔬 SOLUTION METHOD:")
        print("-" * 90)
        print(problem.solution_method.strip())

        print(f"\n🏷️  RELATED FIELDS:")
        print("-" * 90)
        for field in problem.related_fields:
            print(f"   • {field}")

        print(f"\n💡 NOTES:")
        print("-" * 90)
        print(problem.notes)

        print("\n" + "=" * 90 + "\n")

    def display_summary(self) -> None:
        """Display a summary of all Hilbert problems with their status."""
        all_problems = self.get_all_problems()

        if not all_problems:
            print("\n⚠️  Could not fetch problems. Please check your API configuration.\n")
            return

        solved = sum(1 for p in all_problems.values() if p.status == ProblemStatus.SOLVED)
        unsolved = sum(1 for p in all_problems.values() if p.status == ProblemStatus.UNSOLVED)
        partial = sum(1 for p in all_problems.values() if p.status == ProblemStatus.PARTIALLY_SOLVED)

        print("\n" + "=" * 90)
        print("HILBERT'S 23 PROBLEMS - SUMMARY")
        print("=" * 90)

        print(f"\n📊 OVERALL STATUS:")
        print(f"   ✅ Solved:           {solved}/23")
        print(f"   ❓ Unsolved:         {unsolved}/23")
        print(f"   ⚠️  Partially Solved: {partial}/23")

        print(f"\n✅ SOLVED PROBLEMS:")
        for num, problem in sorted(all_problems.items()):
            if problem.status == ProblemStatus.SOLVED:
                print(f"   {num:2d}. {problem.title}")

        print(f"\n❓ UNSOLVED PROBLEMS:")
        for num, problem in sorted(all_problems.items()):
            if problem.status == ProblemStatus.UNSOLVED:
                print(f"   {num:2d}. {problem.title}")

        print(f"\n⚠️  PARTIALLY SOLVED PROBLEMS:")
        for num, problem in sorted(all_problems.items()):
            if problem.status == ProblemStatus.PARTIALLY_SOLVED:
                print(f"   {num:2d}. {problem.title}")

        print("\n" + "=" * 90 + "\n")


def main():
    """Main entry point for the Hilbert problems reference guide."""
    parser = argparse.ArgumentParser(
        description="Hilbert's 23 Problems Reference Guide - Dynamically fetches comprehensive documentation from Perplexity API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hilbert_problems.py                           # Show all problems summary
  python hilbert_problems.py 1                         # Show details of problem 1
  python hilbert_problems.py 8                         # Show Riemann Hypothesis (Problem 8)
        """
    )

    parser.add_argument(
        "problem",
        nargs="?",
        type=int,
        help="Problem number (1-23) to display details"
    )

    args = parser.parse_args()

    try:
        # Initialize the guide
        guide = HilbertProblemsGuide()

        # Display specific problem or summary
        if args.problem:
            if args.problem < 1 or args.problem > 23:
                print(f"\n❌ Invalid problem number: {args.problem}")
                print("Please specify a number between 1 and 23\n")
                return

            print(f"\n🔄 Fetching Problem {args.problem}...")
            problem = guide.get_problem(args.problem)
            HilbertProblemsGuide.display_problem(problem)
        else:
            guide.display_summary()

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
