# Quick Start Guide - Refactored Perplexity CLI

## What Changed?

Your codebase has been refactored to eliminate redundancy and improve consistency. Here's what you need to know:

---

## New Files to Know About

### `shared_utils.py`
Centralized utilities used by all CLI tools:
```python
from shared_utils import (
    print_success,        # Print success messages with ✓
    print_error,          # Print errors with ❌ and exit
    print_response,       # Format and print responses
    print_search,         # Print search status with 🔍
    SEPARATOR,            # Standard "=" * 60
    validate_not_empty,   # Validate non-empty strings
)
```

### `cli_base.py`
Base class for building CLI tools (optional, for future development):
```python
from cli_base import BasePerplex CLI

class MyCustomTool(BasePerplex CLI):
    def setup_parser(self):
        # Your argument parsing
        pass

    def run(self):
        # Your logic
        pass
```

---

## Updated Client API

The `PerplexityTextClient` now has convenient wrapper methods:

### Simple Query
```python
from text_client import PerplexityTextClient

client = PerplexityTextClient()
response = client.query("What is quantum computing?")
print(response)
```

### Reasoning
```python
from text_client import PerplexityTextClient, ReasoningEffort

client = PerplexityTextClient()
response = client.reason(
    "Explain why the sky is blue",
    effort=ReasoningEffort.HIGH,
    use_pro=True,
    step_by_step=True
)
print(response)
```

### Research
```python
from text_client import PerplexityTextClient, ResearchDepth

client = PerplexityTextClient()
response = client.research(
    "Climate change impacts",
    depth=ResearchDepth.COMPREHENSIVE,
    sources=["IPCC reports", "scientific journals"]
)
print(response)
```

### Chat with History
```python
client = PerplexityTextClient()
history = []

response = client.chat(
    "Hello!",
    conversation_history=history,
    creative=False
)

# Continue conversation
response = client.chat(
    "Tell me more",
    conversation_history=history,
    creative=False
)
```

---

## CLI Scripts - What's New?

All scripts are simpler and more consistent. They all follow this pattern:

### `perplx_reasoning.py`
```bash
# Default question
python perplx_reasoning.py

# Custom question
python perplx_reasoning.py -q "Why is the sky blue?"

# From file
python perplx_reasoning.py -f questions.txt -o responses.txt
```

### `perplx_research.py`
```bash
# Basic research
python perplx_research.py -q "AI ethics"

# Deep research
python perplx_research.py -q "Climate change" -d COMPREHENSIVE

# With specific sources
python perplx_research.py -q "AI" -s "Research papers" "News articles"
```

### `perplx_query.py`
```bash
# Single query
python perplx_query.py -q "What is AI?"

# Batch from file
python perplx_query.py -f questions.txt

# Save to custom file
python perplx_query.py -f questions.txt -o my_results.txt
```

### `perplx_chat.py`
```bash
# Interactive chat
python perplx_chat.py

# Start with a message
python perplx_chat.py --initial "Hello"

# Creative mode
python perplx_chat.py --creative

# Save to specific file
python perplx_chat.py --output chat.txt

# Continue previous conversation
python perplx_chat.py --input chat.txt
```

### `domain_search.py`
```bash
# Find domains for a query
python domain_search.py "quantum computing"

# Get top 10 domains
python domain_search.py "AI" --count 10

# Save to custom file
python domain_search.py "climate science" -o results.json
```

---

## Key Improvements

### Before vs After

**Error Handling**
```python
# Before - scattered across files
except ValueError as e:
    print(f"❌ Error: {e}")
    print("Please ensure your PERPLEXITY_API_KEY is set as an environment variable.")

# After - centralized
from shared_utils import handle_api_error
except ValueError as e:
    handle_api_error(e, "client initialization")
```

**Response Formatting**
```python
# Before - custom in each file
header = "=" * 20 + " RESPONSE " + "=" * 20
footer = "=" * 60
print(f"{header}\n{response}\n{footer}")

# After - consistent
from shared_utils import print_response
print_response("RESPONSE", response)
```

**Separators**
```python
# Before - inconsistent (53, 59, 60 chars!)
RESPONSE_SEPARATOR = "=" * 53
BATCH_SEPARATOR = "=" * 60

# After - single standard
from shared_utils import SEPARATOR  # Always 60 chars
```

---

## Code Organization

```
text/
├── text_client.py           # Main Perplexity client (enhanced)
├── shared_utils.py          # NEW: Centralized utilities
├── cli_base.py              # NEW: Base CLI class (for future)
├── perplx_reasoning.py      # Refactored
├── perplx_research.py       # Refactored
├── perplx_query.py          # Refactored
├── perplx_chat.py           # Refactored
├── domain_search.py         # Refactored
├── perplx_search.py         # Unchanged
├── REFACTORING_SUMMARY.md   # Detailed changes
└── QUICK_START.md           # This file
```

---

## Backward Compatibility

✅ **All changes are backward compatible**

- Old code will still work
- New wrapper methods don't break existing functionality
- Existing scripts have been updated to use shared utilities
- You can migrate existing code gradually

---

## Common Patterns

### Input Validation
```python
from shared_utils import validate_not_empty

try:
    prompt = validate_not_empty(user_input, "Prompt")
except ValueError as e:
    print(f"Invalid input: {e}")
```

### Status Messaging
```python
from shared_utils import print_success, print_error, print_search

print_success("Operation completed")
print_error("Something went wrong")
print_search("Searching for results...")
```

### Response Display
```python
from shared_utils import print_response, print_list_response

# Single response
print_response("TITLE", "Content here...")

# List of items
items = ["item1", "item2", "item3"]
print_list_response("ITEMS", items)
```

---

## Troubleshooting

**ImportError with shared_utils or cli_base?**
- Make sure both files are in the same directory as your scripts
- Add the directory to PYTHONPATH if running from elsewhere

**Different output formatting?**
- This is intentional - now using consistent, cleaner formatting
- Standard separator width is 60 characters
- All responses follow the same pattern

**Missing PERPLEXITY_API_KEY error?**
- Set the environment variable: `export PERPLEXITY_API_KEY=your_key`
- Error messages now explicitly guide you on this

---

## Next Steps

1. **Test the refactored scripts** - They work the same but cleaner
2. **Use the new client API** - Easier wrapper methods available
3. **Import shared_utils** - For consistent formatting in new code
4. **Check REFACTORING_SUMMARY.md** - For detailed changes
5. **Read the docstrings** - Every function is documented

---

## Need Help?

- Check docstrings: `python -c "from text_client import PerplexityTextClient; help(PerplexityTextClient.reason)"`
- Run with `--help`: `python perplx_reasoning.py --help`
- See examples in script files
- Review REFACTORING_SUMMARY.md for detailed documentation

Enjoy the cleaner codebase! 🚀
