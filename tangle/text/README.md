# Perplexity CLI - Refactored Edition

A simplified, powerful set of command-line tools for interacting with Perplexity AI.

## Quick Start

### Installation
```bash
export PERPLEXITY_API_KEY=your_api_key_here
```

### Usage Examples

#### Query
```bash
python perplx_query.py -q "What is quantum computing?"
python perplx_query.py -f questions.txt -o results.txt
```

#### Reasoning
```bash
python perplx_reasoning.py -q "Why is the sky blue?"
python perplx_reasoning.py -f questions.txt -o reasoning.txt
```

#### Research
```bash
python perplx_research.py -q "AI ethics" -d COMPREHENSIVE
python perplx_research.py -q "Climate change" -s "Scientific papers"
```

#### Chat
```bash
python perplx_chat.py                              # Interactive
python perplx_chat.py --initial "What is AI?"      # Start with message
python perplx_chat.py --input previous_chat.txt    # Continue conversation
```

---

## Python API

### Simple Query
```python
from text_client import PerplexityTextClient

client = PerplexityTextClient()
response = client.query("What is AI?")
print(response)
```

### Reasoning
```python
from text_client import PerplexityTextClient, ReasoningEffort

client = PerplexityTextClient()
response = client.reason(
    "Solve: 2x + 5 = 15",
    effort=ReasoningEffort.HIGH
)
```

### Research
```python
from text_client import PerplexityTextClient, ResearchDepth

client = PerplexityTextClient()
response = client.research(
    "Climate change impacts",
    depth=ResearchDepth.COMPREHENSIVE,
    sources=["Scientific papers", "Government reports"]
)
```

### Chat with History
```python
client = PerplexityTextClient()
history = []

response = client.chat("Hello", conversation_history=history)
history.append({"role": "user", "content": "Hello"})
history.append({"role": "assistant", "content": response})

response = client.chat("Tell me more", conversation_history=history, creative=True)
```

---

## API Methods

### `client.query(prompt: str) -> str`
Execute a simple query and get a response.

```python
response = client.query("What is machine learning?")
```

### `client.reason(prompt: str, effort=MEDIUM, use_pro=True, step_by_step=True) -> str`
Get step-by-step reasoning about a question.

- `effort`: `ReasoningEffort.LOW` | `MEDIUM` | `HIGH`
- `use_pro`: Use pro model (recommended)
- `step_by_step`: Request explicit reasoning steps

```python
response = client.reason("Why is the sky blue?", effort=ReasoningEffort.HIGH)
```

### `client.research(topic: str, depth=STANDARD, sources=None) -> str`
Conduct deep research on a topic with citations.

- `depth`: `ResearchDepth.BRIEF` | `STANDARD` | `COMPREHENSIVE`
- `sources`: List of source types to emphasize

```python
response = client.research("AI ethics", depth=ResearchDepth.COMPREHENSIVE)
```

### `client.chat(message: str, conversation_history=None, creative=False) -> str`
Have a conversation with history support.

- `conversation_history`: List of previous messages
- `creative`: Higher temperature for more creative responses

```python
response = client.chat("Hello", conversation_history=history, creative=True)
```

---

## Utilities

### Printing
```python
from shared_utils import success, error, info, search, summary, section

success("Done!")              # ✓ Done!
error("Failed")               # ❌ Failed
info("Processing...")         # ℹ Processing...
search("Searching...")        # 🔍 Searching...
summary("Summary")            # 📊 Summary
section("TITLE", "content")   # Formatted section
```

### Validation
```python
from shared_utils import not_empty, in_range

topic = not_empty(input, "Topic")        # Validates non-empty
count = in_range(num, 1, 20, "Count")    # Validates 1-20
```

### Formatting
```python
from shared_utils import format_list, format_dict, SEPARATOR, INDENT

items = format_list(["item1", "item2"])
data = format_dict({"key": "value"})
print(SEPARATOR)  # 60 character separator
```

---

## Files

### Core
- **`text_client.py`** - Main Perplexity client with 4 high-level methods
- **`shared_utils.py`** - Utilities for printing, validation, formatting

### CLI Tools
- **`perplx_query.py`** - Simple queries (single or batch)
- **`perplx_reasoning.py`** - Step-by-step reasoning
- **`perplx_research.py`** - Deep research with citations
- **`perplx_chat.py`** - Interactive conversations
- **`domain_search.py`** - Find authoritative domains for topics

### Optional
- **`cli_base.py`** - Base class for building new CLI tools (optional)

### Documentation
- **`AGGRESSIVE_REFACTORING_SUMMARY.md`** - Details of refactoring changes
- **`README.md`** - This file

---

## Design Principles

### Simplicity
- No configuration objects
- No parameter overload
- Just call the right method

### Clarity
- Task-specific methods
- Self-documenting code
- Clear error messages

### Usability
- Works out of the box
- Smart defaults
- Minimal setup

---

## Example: Complete Script

```python
#!/usr/bin/env python3

from text_client import PerplexityTextClient, ReasoningEffort, ResearchDepth
from shared_utils import success, error, section

def main():
    try:
        client = PerplexityTextClient()
        success("Client initialized")

        # Simple query
        print("\n--- Query ---")
        response = client.query("What is AI?")
        print(response[:200] + "...")

        # Reasoning
        print("\n--- Reasoning ---")
        response = client.reason(
            "Why is the sky blue?",
            effort=ReasoningEffort.HIGH
        )
        print(response[:200] + "...")

        # Research
        print("\n--- Research ---")
        response = client.research(
            "Climate change",
            depth=ResearchDepth.COMPREHENSIVE
        )
        print(response[:200] + "...")

        # Chat
        print("\n--- Chat ---")
        history = []
        response = client.chat("What is quantum computing?", conversation_history=history)
        print(response[:200] + "...")

        success("All examples completed")

    except Exception as e:
        error(f"Error: {e}")

if __name__ == "__main__":
    main()
```

---

## Refactoring Summary

This codebase has been aggressively refactored to remove backward compatibility and maximize simplicity:

- **45% fewer lines of code** (1,308 → 724 lines)
- **50+ functions eliminated**
- **30+ configuration parameters → 4 simple methods**
- **Cleaner, more maintainable code**

For details, see `AGGRESSIVE_REFACTORING_SUMMARY.md`.

---

## Requirements

- Python 3.7+
- `perplexity-ai` package
- `PERPLEXITY_API_KEY` environment variable

---

## License

Your project
