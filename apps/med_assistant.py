#!/usr/bin/env python3
"""
Interactive Medical Consultation using Perplexity API.

Provides evidence-based medical information through an interactive chat
interface with conversation history, session management, and trusted
medical source filtering.

Usage:
  python medhelp.py                    # Start interactive session
  python medhelp.py -m sonar           # Use sonar model
  python medhelp.py -v                 # Verbose logging
  python medhelp.py --no-auto-save     # Disable auto-save

Interactive Commands:
  /add-attachment <path>  - Attach medical image or PDF
  /remove-attachment      - Remove attachment
  /history [N]            - Show conversation history
  /clear                  - Clear conversation
  /stats                  - Show session statistics
  /save [path]            - Save session
  /load <path>            - Load session
  /quit                   - Exit session
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# Add tangle module to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tangle"))

from perplx_chat import PerplexityChat, interactive_chat
from config import ModelConfig, ChatConfig, SearchFilter, ModelOutput
from logging_utils import setup_logging

logger = setup_logging("medhelp.log")

# Medical system prompt for all sessions
MEDICAL_SYSTEM_PROMPT = (
    "You are a trusted medical assistant.\n"
    "Provide only evidence-based, concise and polite answers.\n"
    "Use clear, professional language.\n"
    "Avoid speculation.\n"
    "Focus on relevance and safety."
)

# Trusted medical domains for search filtering
TRUSTED_MEDICAL_DOMAINS = [
    "mayoclinic.org/drugs-supplements",
    "mayoclinic.org",
    "clevelandclinic.org",
    "medlineplus.gov",
    "healthline.com",
    "drugs.com",
    "webmd.com/drugs",
    "webmd.com",
    "cdc.gov",
    "ncbi.nlm.nih.gov",
    "ema.europa.eu",
    "uptodate.com",
    "fda.gov",
    "rxlist.com",
    "nih.gov",
]


class MedicalChat(PerplexityChat):
    """Medical chat extending PerplexityChat with automatic domain filtering."""

    def __init__(self, model: str = "sonar-pro", auto_save: bool = True):
        """Initialize medical chat session.

        Args:
            model: Model to use (default: sonar-pro)
            auto_save: Auto-save sessions on exit (default: True)
        """
        model_config = ModelConfig(
            model=model,
            temperature=0.2,
            max_tokens=2000
        )

        chat_config = ChatConfig(
            max_history=20,
            auto_save=auto_save,
            save_dir="outputs"
        )

        super().__init__(model_config, chat_config)
        self.set_system_prompt(MEDICAL_SYSTEM_PROMPT)
        self.medical_filter = SearchFilter(allowed_domains=TRUSTED_MEDICAL_DOMAINS)

        logger.info(f"MedicalChat initialized with model: {model}")

    def send_message(
        self,
        user_message: str,
        image_paths: Optional[List[str]] = None,
        pdf_path: Optional[str] = None,
        search_filter: Optional[SearchFilter] = None,
        config: Optional[ModelConfig] = None
    ) -> ModelOutput:
        """Override to inject medical filter if no custom filter provided."""
        if search_filter is None:
            search_filter = self.medical_filter
        return super().send_message(user_message, image_paths, pdf_path, search_filter, config)

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Interactive Medical Consultation using Perplexity API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Interactive medical assistant providing evidence-based information from
trusted sources: Mayo Clinic, CDC, Cleveland Clinic, FDA, NIH, and more.

Examples:
  %(prog)s                    # Start with default model (sonar-pro)
  %(prog)s -m sonar           # Use sonar model
  %(prog)s --no-auto-save     # Disable auto-save on exit
        """
    )

    parser.add_argument(
        "-m", "--model",
        type=str,
        default="sonar-pro",
        help="Model to use (default: sonar-pro)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-auto-save",
        action="store_true",
        help="Disable automatic session saving on exit"
    )

    return parser


def main():
    """Main entry point for interactive medical consultation."""
    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        print("\nInitializing Medical Assistant...")

        # Initialize medical chat
        medical_chat = MedicalChat(
            model=args.model,
            auto_save=not args.no_auto_save
        )

        # Display medical welcome banner
        print("=" * 70)
        print("Medical Assistant - Interactive Consultation Session")
        print("=" * 70)
        print("This assistant provides evidence-based medical information")
        print("from trusted sources including Mayo Clinic, CDC, Cleveland Clinic,")
        print("FDA, NIH, and other authoritative medical domains.")
        print()
        print("DISCLAIMER: This assistant provides information only and does not")
        print("replace professional medical advice. Always consult with qualified")
        print("healthcare professionals for medical decisions.")
        print()
        print("Commands: /help for list of commands, /quit to exit")
        print("=" * 70)
        print()

        # Start interactive chat session
        interactive_chat(medical_chat)

        # Handle auto-save on clean exit
        if medical_chat.chat_config.auto_save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"outputs/medical_session_{timestamp}.json"
            saved_path = medical_chat.save_session(filepath)
            print(f"\nMedical session saved to: {saved_path}")

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        print(f"\n❌ Configuration Error: {str(e)}\n", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user\n", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\n❌ Unexpected error: {str(e)}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
