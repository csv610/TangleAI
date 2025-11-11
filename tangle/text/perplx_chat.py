"""
Perplexity Chat CLI - Interactive multi-turn conversations.

Supports conversation history and creative mode.
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from text_client import PerplexityTextClient
from shared_utils import success, error, summary, SEPARATOR


def load_conversation(file_path: str) -> list:
    """Load conversation history from a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Parse messages in USER: / ASSISTANT: format
    content = path.read_text()
    pattern = r'(USER|ASSISTANT):\n(.*?)(?=\n(USER|ASSISTANT):|$)'
    matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)

    messages = [
        {"role": match.group(1).lower(), "content": match.group(2).strip()}
        for match in matches
    ]

    if not messages:
        raise ValueError("No valid messages found in file")

    return messages


def save_conversation(messages: list, file_path: str) -> None:
    """Save conversation to a file."""
    path = Path(file_path)

    # Add header if new file
    if not path.exists():
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        path.write_text(f"\n{SEPARATOR}\nConversation - {timestamp}\n{SEPARATOR}\n\n")

    # Append messages
    with open(path, 'a') as f:
        for msg in messages:
            role = msg["role"].upper()
            f.write(f"{role}:\n{msg['content']}\n\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive chat with Perplexity AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python perplx_chat.py
  python perplx_chat.py --initial "What is AI?"
  python perplx_chat.py --creative
  python perplx_chat.py --input previous_chat.txt
        """
    )

    parser.add_argument("--initial", help="Initial message to start with")
    parser.add_argument("--creative", action="store_true", help="Enable creative mode")
    parser.add_argument("--output", help="Save conversation to file (default: chat_[DATE].txt)")
    parser.add_argument("--input", help="Load previous conversation")

    args = parser.parse_args()

    # Determine output file
    output_file = args.output or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    try:
        client = PerplexityTextClient()
        success("Client initialized")
        print("Type 'exit', 'quit', or 'bye' to end conversation\n")

        # Load previous conversation if provided
        conversation = []
        if args.input:
            conversation = load_conversation(args.input)
            success(f"Loaded {len(conversation)} messages from {args.input}\n")
            if len(conversation) >= 2:
                print(f"Last exchange:\n  {conversation[-2]['content'][:60]}...\n  {conversation[-1]['content'][:60]}...\n")

        turn_count = 0

        # Get first message
        if args.initial:
            user_message = args.initial
            print(f"You: {user_message}")
        else:
            user_message = input("You: ").strip()
            if not user_message:
                print("No input. Exiting.")
                return

        # Chat loop
        while True:
            if user_message.lower() in ['exit', 'quit', 'bye']:
                success("Conversation ended")
                break

            try:
                # Get response
                response = client.chat(user_message, conversation_history=conversation, creative=args.creative)

                # Save messages
                conversation.append({"role": "user", "content": user_message})
                conversation.append({"role": "assistant", "content": response})

                save_conversation(
                    [{"role": "user", "content": user_message}, {"role": "assistant", "content": response}],
                    output_file
                )

                print(f"\nAssistant: {response}\n")
                turn_count += 1

            except Exception as e:
                error(f"Error: {e}", exit_code=0)
                retry = input("Try again? (yes/no): ").strip().lower()
                if retry != 'yes':
                    break
                user_message = input("You: ").strip()
                if not user_message:
                    break
                continue

            # Get next message
            user_message = input("You: ").strip()
            if not user_message:
                continue

        # Summary
        if conversation:
            summary(f"Conversation Summary\n   Turns: {turn_count}\n   Messages: {len(conversation)}\n   Saved to: {output_file}")

    except Exception as e:
        error(f"Error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        success("Chat interrupted by user")
        sys.exit(0)
