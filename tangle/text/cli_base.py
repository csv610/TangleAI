"""
Optional base class for CLI tools (not actively used).

Provided as a template for future CLI development.
New CLI tools are simpler to write directly without this class.
"""

import argparse
import sys
from abc import ABC, abstractmethod
from text_client import PerplexityTextClient
from shared_utils import error


class BaseCLI(ABC):
    """Optional base class for CLI tools."""

    def __init__(self, description: str):
        self.description = description
        self.parser = None
        self.args = None
        self.client = None

    def setup_parser(self) -> argparse.ArgumentParser:
        """Override in subclass."""
        return argparse.ArgumentParser(description=self.description)

    @abstractmethod
    def run(self) -> None:
        """Override in subclass."""
        pass

    def initialize_client(self) -> PerplexityTextClient:
        """Initialize Perplexity client."""
        try:
            self.client = PerplexityTextClient()
            return self.client
        except ValueError as e:
            error(f"Failed to initialize client: {e}")

    def execute(self) -> int:
        """Execute the CLI tool."""
        try:
            self.parser = self.setup_parser()
            self.args = self.parser.parse_args()
            self.initialize_client()
            self.run()
            return 0
        except KeyboardInterrupt:
            print("\nInterrupted")
            return 1
        except Exception as e:
            error(f"Error: {e}")
            return 1

    def main(self) -> None:
        """Entry point."""
        exit_code = self.execute()
        sys.exit(exit_code)
