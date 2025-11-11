# Perplexity AI Python Toolkit

A comprehensive Python client and toolkit for the Perplexity AI API. Provides easy access to multiple AI capabilities including simple queries, step-by-step reasoning, deep research, interactive chat, and specialized processing for text, PDFs, and images.

## Features

### Core Capabilities
- **Simple Queries** - Ask questions and get instant responses
- **Step-by-Step Reasoning** - Get detailed logical analysis with multiple reasoning effort levels
- **Deep Research** - Comprehensive research with sources and citations at various depth levels
- **Interactive Chat** - Multi-turn conversations with history management
- **Advanced Search** - Powerful search with 30+ configurable parameters, domain filtering, and geographic targeting

### Specialized Processing
- **PDF Processing** - Extract chapters, learn from books, analyze academic papers
- **Image Processing** - Process and analyze images
- **Medicine Lookup** - Comprehensive medicine and drug information from multiple APIs (OpenFDA, RxNav, PubChem, DrugBank)
- **Domain Discovery** - Intelligently identify authoritative domains for any topic

### Developer-Friendly
- **Configuration Management** - Robust `ModelConfig` with validation and factory methods
- **CLI Tools** - Command-line interfaces for all major features
- **Utility Libraries** - Pydantic helpers, prompt generation, formatting utilities
- **Error Handling** - Automatic retry logic with exponential backoff

## Installation

### Prerequisites
- Python 3.7 or higher
- Perplexity API key (get one at [Perplexity](https://perplexity.com/api))

### Install the Package

```bash
# Clone the repository
git clone <repository-url>
cd Perplexity

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Set Up API Key

```bash
# Export your Perplexity API key
export PERPLEXITY_API_KEY="your-api-key-here"

# Or add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export PERPLEXITY_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Quick Start

### Using the Python API

```python
from tangle.text.text_client import PerplexityTextClient, ReasoningEffort, ResearchDepth

# Initialize client
client = PerplexityTextClient()

# Simple query
response = client.query("What is quantum computing?")
print(response)

# Step-by-step reasoning
response = client.reason(
    "Why is the sky blue?",
    effort=ReasoningEffort.HIGH,
    step_by_step=True
)
print(response)

# Deep research
response = client.research(
    "Latest breakthroughs in AI",
    depth=ResearchDepth.COMPREHENSIVE
)
print(response)

# Interactive chat
messages = []
response = client.chat("Hello, how can you help?", messages)
print(response)
```

### Using Configuration

```python
from perplx import ModelConfig

# Create a configuration for reasoning
config = ModelConfig(
    model="sonar-reasoning-pro",
    temperature=0.3,
    max_tokens=2000,
    reasoning_effort="high"
)

# Create a configuration for research
research_config = ModelConfig.create_research_config(depth="comprehensive")

# Or use factory method for reasoning
reasoning_config = ModelConfig.create_reasoning_config(effort="high")
```

### Advanced Search

```python
from tangle.text.perplx_search import PerplexitySearchClient, Config

# Create a search configuration
config = Config(
    max_results=10,
    search_mode="web",
    temperature=0.2
).set_domain_filter_by_query("quantum computing", count=10)

# Initialize client
client = PerplexitySearchClient(config)

# Perform search
results = client.search("latest quantum computing developments")

# Batch search
queries = [
    "quantum computing applications",
    "quantum error correction",
    "quantum algorithms"
]
results = client.batch_search(queries)
client.save_results_json(results, "results.json")
```

### CLI Tools

Each major feature has a command-line interface:

```bash
# Simple queries
python tangle/text/perplx_query.py -q "What is machine learning?"

# Reasoning
python tangle/text/perplx_reasoning.py -q "Explain quantum entanglement"

# Research
python tangle/text/perplx_research.py -q "Recent AI breakthroughs"

# Interactive chat
python tangle/text/perplx_chat.py

# Batch processing
python tangle/text/perplx_query.py -f questions.txt -o answers.txt
```

## Configuration Options

### ModelConfig Parameters

```python
ModelConfig(
    # Core parameters
    model="sonar-pro",              # Model to use
    temperature=0.7,                # Response randomness (0.0-1.0)
    max_tokens=2000,                # Maximum response length
    system_prompt="...",            # System instructions

    # Reasoning parameters
    reasoning_effort="medium",      # low | medium | high
    use_step_by_step=True,          # Enable step-by-step reasoning

    # Research parameters
    research_depth="standard",      # brief | standard | comprehensive

    # Conversation parameters
    conversation_history=[...]      # Previous messages
)
```

### Search Config Parameters

The `Config` class in `perplx_search.py` provides 30+ parameters organized by category:

```python
Config(
    # Search Results (2 params)
    max_results=10,
    search_domain_filter=["nature.com"],

    # Geographic & Language (6 params)
    iso_country_code="US",
    language_preference="en",
    user_location_latitude=None,
    user_location_longitude=None,
    user_location_region=None,
    user_location_city=None,

    # Date Filtering (5 params)
    search_recency_filter="month",  # day | week | month | year
    search_after_date="01/01/2024",
    search_before_date="12/31/2024",
    last_updated_after=None,
    last_updated_before=None,

    # LLM Control (7 params)
    temperature=0.2,
    max_tokens=None,
    top_p=0.9,
    presence_penalty=0.0,
    frequency_penalty=0.0,
    # ... and more
)
```

## Project Structure

```
Perplexity/
├── README.md                       # This file
├── setup.py                        # Package configuration
├── Makefile                        # Development tasks
├── perplx.py                       # Core ModelConfig class
├── examples/                       # Example utilities
│   ├── pydantic_utils.py
│   ├── simple_prompt_gen.py
│   ├── markdown_model_doc.py
│   ├── city_info.py
│   └── test_*.py
└── tangle/                         # Main modules
    ├── text/                       # Text processing
    │   ├── text_client.py          # Main client
    │   ├── perplx_search.py        # Advanced search
    │   ├── domain_search.py        # Domain discovery
    │   ├── perplx_query.py         # Query CLI
    │   ├── perplx_reasoning.py     # Reasoning CLI
    │   ├── perplx_research.py      # Research CLI
    │   ├── perplx_chat.py          # Chat CLI
    │   ├── shared_utils.py         # Utilities
    │   └── cli_base.py             # Base CLI class
    ├── pdf/                        # PDF processing
    │   ├── pdf_client.py
    │   ├── extract_book_chapter.py
    │   ├── learn_book.py
    │   ├── paper_review.py
    │   └── base classes
    ├── image/                      # Image processing
    │   └── image_client.py
    ├── medicine_lookup.py          # Medicine information
    └── drugbank_medicine.py        # DrugBank integration
```

## Models Supported

- **sonar** - Fast, compact model for quick queries
- **sonar-pro** - Balanced model with better reasoning
- **sonar-reasoning** - Enhanced reasoning for complex analysis
- **sonar-reasoning-pro** - Professional-grade reasoning
- **sonar-deep-research** - Comprehensive research with sources

## API Reference

### PerplexityTextClient

```python
client.query(prompt: str) -> str
    """Execute a simple query."""

client.reason(
    prompt: str,
    effort: Optional[ReasoningEffort] = None,
    use_pro: bool = True,
    step_by_step: bool = True
) -> str
    """Get step-by-step reasoning."""

client.research(
    prompt: str,
    depth: Optional[ResearchDepth] = None,
    use_pro: bool = True
) -> str
    """Get deep research with sources."""

client.chat(
    prompt: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None
) -> str
    """Interactive chat with history."""
```

### PerplexitySearchClient

```python
client.search(query: str)
    """Perform a single search."""

client.batch_search(queries: List[str])
    """Run multiple queries with delays."""

client.discover_domains(
    query: str,
    count: int = 10
) -> DomainResult
    """Discover authoritative domains."""

client.save_results_json(responses, output_path: str)
    """Save results to JSON file."""
```

## Examples

### Example 1: Research a Topic

```python
from tangle.text.text_client import PerplexityTextClient, ResearchDepth

client = PerplexityTextClient()
result = client.research(
    "How do transformers work in machine learning?",
    depth=ResearchDepth.COMPREHENSIVE
)
print(result)
```

### Example 2: Batch Queries

```python
from tangle.text.perplx_search import PerplexitySearchClient, Config

config = Config(max_results=5)
client = PerplexitySearchClient(config)

questions = [
    "What is quantum computing?",
    "How do quantum computers differ from classical computers?",
    "What are quantum algorithms?"
]

results = client.batch_search(questions)
client.save_results_json(results, "quantum_research.json")
```

### Example 3: Domain-Specific Search

```python
from tangle.text.perplx_search import PerplexitySearchClient, Config

# Automatically discover authoritative domains for the topic
config = Config(max_results=10).set_domain_filter_by_query(
    "machine learning in healthcare",
    count=8
)

client = PerplexitySearchClient(config)
results = client.search("latest machine learning applications in healthcare")
```

### Example 4: Interactive Chat

```python
from tangle.text.text_client import PerplexityTextClient

client = PerplexityTextClient()

# Start a conversation
messages = []
while True:
    user_input = input("You: ")
    if user_input.lower() in ['exit', 'quit']:
        break

    response = client.chat(user_input, messages)
    print(f"AI: {response}")

    # Update message history
    messages.append({"role": "user", "content": user_input})
    messages.append({"role": "assistant", "content": response})
```

## Development

### Run Tests

```bash
make test
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check
```

### Build and Install

```bash
# Build the package
make build

# Install in development mode
make install

# Clean build artifacts
make clean
```

## Common Issues

### "API key must be set"

Make sure `PERPLEXITY_API_KEY` environment variable is set:

```bash
export PERPLEXITY_API_KEY="your-api-key"
```

### "perplexity package is required"

Install the Perplexity SDK:

```bash
pip install perplexity-ai
```

### Rate Limiting

The toolkit includes automatic retry logic with exponential backoff. If you encounter rate limiting, the client will automatically retry with delays.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation in the docstrings
- Review examples in the `examples/` directory

## Changelog

### Version 0.1.0 (Initial Release)
- Core text client with query, reasoning, research, and chat
- Advanced search with 30+ configuration parameters
- Domain discovery and filtering
- PDF processing capabilities
- Image processing support
- Medicine/drug lookup system
- CLI tools for all major features
- Comprehensive error handling and retry logic
