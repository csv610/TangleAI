# Perplexity AI Python Toolkit

A comprehensive Python client and toolkit for the Perplexity AI API. Provides easy access to querying, reasoning, research, and specialized AI applications with support for text, PDFs, and images.

## Features

### Core Client (`PerplexityClient`)
- **Flexible Configuration** - `ModelConfig` with 13+ parameters for fine-grained control
- **Search Filtering** - High-level `SearchFilter` abstraction for domain and date filtering
- **Structured Output** - Pydantic-based response models with JSON schema validation
- **Multi-modal Input** - Support for text, images, and PDF documents
- **Parameter Control** - Temperature, penalties, reasoning effort, language preference, and more

### Specialized Applications
- **Disease QA** - Medical question answering with structured disease information
- **Research Finder** - Discovers authoritative sources and performs in-depth research
- **Daily Knowledge Bot** - Aggregates and summarizes daily knowledge on topics
- **Fact Checker** - Validates claims with structured output verification
- **Paper Review** - Analyzes academic papers with detailed summaries
- **Medicine Lookup** - Comprehensive medicine and drug information

### Developer-Friendly
- **Comprehensive Tests** - 94+ parameter-focused unit tests
- **Type-Safe Configuration** - Dataclass-based configs with validation
- **CLI Support** - Command-line interface for the main client
- **Error Handling** - Proper exception handling and validation

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

### Basic Usage

```python
from tangle.perplx_client import PerplexityClient
from tangle.config import ModelConfig, ModelInput

# Initialize client
client = PerplexityClient()

# Simple query
model_input = ModelInput(user_prompt="What is quantum computing?")
response = client.generate_content(model_input)
print(response.choices[0].message.content)

# Query with custom configuration
config = ModelConfig(
    model="sonar-pro",
    temperature=0.7,
    max_tokens=2048
)
response = client.generate_content(model_input, config)
print(response.choices[0].message.content)

# Query with system prompt
model_input = ModelInput(
    user_prompt="Explain quantum entanglement",
    system_prompt="You are a physics expert. Explain concepts clearly."
)
response = client.generate_content(model_input, config)
print(response.choices[0].message.content)
```

### Using Search Filters

```python
from tangle.perplx_client import PerplexityClient
from tangle.config import ModelConfig, ModelInput, SearchFilter

client = PerplexityClient()

# Filter search results by domain and recency
search_filter = SearchFilter(
    allowed_domains=["arxiv.org", "scholar.google.com"],
    recency="month"
)

model_input = ModelInput(user_prompt="Recent breakthroughs in machine learning")
config = ModelConfig(return_related_questions=True)

response = client.generate_content(model_input, config, search_filter)
print(response.choices[0].message.content)
```

### Structured Output

```python
from pydantic import BaseModel
from tangle.perplx_client import PerplexityClient
from tangle.config import ModelInput

class ResearchResult(BaseModel):
    topic: str
    summary: str
    key_findings: list[str]
    sources: list[str]

client = PerplexityClient()

model_input = ModelInput(
    user_prompt="Research recent AI breakthroughs",
    response_model=ResearchResult
)

response = client.generate_content(model_input)
result = ResearchResult.model_validate_json(response.choices[0].message.content)
print(result)
```

### CLI Tools

```bash
# Query the Perplexity API with custom configuration
python tangle/perplx_client.py -q "What is quantum computing?" \
  -s "You are a physics expert" \
  -m sonar-pro \
  -t 0.7 \
  --max-tokens 2048
```

## Configuration Options

### ModelConfig Parameters (13 parameters)

```python
config = ModelConfig(
    # Model selection
    model="sonar",                  # Model name (sonar, sonar-pro)

    # Core sampling parameters
    temperature=0.7,                # Randomness (0.0-2.0), default 0.7
    top_p=0.9,                      # Nucleus sampling (0.0-1.0), default 0.9
    max_tokens=1024,                # Max response length, default 1024

    # Streaming
    stream=False,                   # Stream responses, default False

    # Search behavior
    search_mode="web",              # web | local, default web
    disable_search=False,           # Disable web search, default False
    language_preference="en",       # Language code (en, es, fr, etc)

    # Advanced reasoning
    reasoning_effort="medium",      # low | medium | high, default medium

    # Response options
    return_images=False,            # Include images in results
    return_related_questions=False, # Include related questions

    # Sampling penalties
    top_k=0,                        # Top-k sampling (0 disabled)
    presence_penalty=0.0,           # Penalize token repetition
    frequency_penalty=0.0           # Penalize frequent tokens
)
```

### SearchFilter Parameters

```python
filter = SearchFilter(
    # Domain filtering (choose one)
    allowed_domains=["nasa.gov", "arxiv.org"],  # Whitelist domains
    blocked_domains=["reddit.com"],              # Blacklist domains

    # Date filtering (choose one approach)
    recency="month",                # day | week | month | year
    # OR
    published_after="3/1/2025",    # Publication date range
    published_before="12/31/2025",
    # OR
    updated_after="3/1/2025",      # Last update date range
    updated_before="12/31/2025"
)
```

### ModelInput Parameters

```python
input_data = ModelInput(
    user_prompt="Your question here",       # Required (unless image/PDF provided)
    system_prompt="Role instructions",      # Optional system prompt
    image_path="/path/to/image.png",        # Optional image file
    pdf_path="/path/to/document.pdf",       # Optional PDF file
    response_model=PydanticModel            # Optional structured output schema
)
```

## Project Structure

```
Perplexity/
├── README.md                       # This file
├── setup.py                        # Package configuration
├── Makefile                        # Development tasks
├── tangle/                         # Core modules
│   ├── perplx_client.py           # Main Perplexity client
│   ├── config.py                  # ModelConfig, ModelInput, SearchFilter
│   ├── image_utils.py             # Image encoding utilities
│   ├── domain_search.py           # Domain discovery
│   ├── country_code.py            # Country code utilities
│   ├── test_perplx_client.py      # 94+ comprehensive tests
│   └── text/                       # Text processing modules (legacy)
└── apps/                           # Specialized applications
    ├── disease_qa.py              # Medical Q&A system
    ├── research_finder.py         # Research discovery
    ├── daily_knowledge_bot.py     # Daily knowledge aggregation
    ├── facts_checker.py           # Fact verification
    ├── paper_review.py            # Academic paper analysis
    ├── medicine_lookup.py         # Medicine information lookup
    ├── drugbank_medicine.py       # DrugBank API integration
    ├── perplx_client_cli.py       # CLI interface
    ├── medhelp.py                 # Medical help application
    └── test_disease_qa.py         # Disease QA tests
```

## Models Supported

- **sonar** - Fast, compact model for quick queries
- **sonar-pro** - Balanced model with better reasoning and capabilities

## API Reference

### PerplexityClient

```python
client = PerplexityClient(config: Optional[ModelConfig] = None)
    """Initialize the Perplexity client with optional default config."""

client.generate_content(
    model_input: ModelInput,
    config: Optional[ModelConfig] = None,
    search_filter: Optional[SearchFilter] = None
) -> ChatCompletion
    """Generate content based on input and configuration.

    Returns a ChatCompletion response with choices[0].message.content
    containing the assistant's response.
    """
```

### Specialized Applications

#### Disease QA
```python
from apps.disease_qa import DiseaseQA

qa = DiseaseQA()
result = qa.answer_disease_question("What are symptoms of diabetes?")
print(result.symptoms, result.treatment_options)
```

#### Research Finder
```python
from apps.research_finder import ResearchFinder

finder = ResearchFinder()
results = finder.find_research("machine learning in healthcare")
```

#### Daily Knowledge Bot
```python
from apps.daily_knowledge_bot import DailyKnowledgeBot

bot = DailyKnowledgeBot()
summary = bot.get_daily_summary("AI breakthroughs")
```

#### Fact Checker
```python
from apps.facts_checker import FactChecker

checker = FactChecker()
result = checker.verify_claim("Machine learning is a subset of AI")
print(result.is_verified, result.confidence)
```

## Examples

### Example 1: Structured Medical Query

```python
from pydantic import BaseModel
from tangle.perplx_client import PerplexityClient
from tangle.config import ModelInput

class DiseaseInfo(BaseModel):
    name: str
    symptoms: list[str]
    treatment_options: list[str]
    severity: str

client = PerplexityClient()

model_input = ModelInput(
    user_prompt="What is type 2 diabetes? Include symptoms and treatments.",
    response_model=DiseaseInfo
)

response = client.generate_content(model_input)
disease_data = DiseaseInfo.model_validate_json(response.choices[0].message.content)
print(f"Disease: {disease_data.name}")
print(f"Symptoms: {disease_data.symptoms}")
print(f"Treatments: {disease_data.treatment_options}")
```

### Example 2: Filtered Research Query

```python
from tangle.perplx_client import PerplexityClient
from tangle.config import ModelConfig, ModelInput, SearchFilter

client = PerplexityClient()

# Research only from academic sources published in the last month
search_filter = SearchFilter(
    allowed_domains=["arxiv.org", "scholar.google.com", "pubmed.gov"],
    recency="month"
)

model_input = ModelInput(
    user_prompt="What are the latest breakthroughs in CRISPR gene therapy?"
)

config = ModelConfig(
    model="sonar-pro",
    temperature=0.5,
    return_related_questions=True
)

response = client.generate_content(model_input, config, search_filter)
print(response.choices[0].message.content)
```

### Example 3: Multi-Modal Query with PDF

```python
from tangle.perplx_client import PerplexityClient
from tangle.config import ModelInput

client = PerplexityClient()

model_input = ModelInput(
    user_prompt="Summarize this research paper and extract the key findings.",
    pdf_path="/path/to/research_paper.pdf",
    system_prompt="You are an expert research analyst. Be concise and precise."
)

response = client.generate_content(model_input)
print(response.choices[0].message.content)
```

### Example 4: Temperature Control for Creativity

```python
from tangle.perplx_client import PerplexityClient
from tangle.config import ModelConfig, ModelInput

client = PerplexityClient()

# Low temperature for factual, deterministic responses
factual_config = ModelConfig(temperature=0.1)
model_input = ModelInput(user_prompt="What is the capital of France?")
response = client.generate_content(model_input, factual_config)

# High temperature for creative responses
creative_config = ModelConfig(temperature=1.5)
model_input = ModelInput(user_prompt="Generate a creative story about AI")
response = client.generate_content(model_input, creative_config)
```

## Testing

The project includes comprehensive tests with 94+ test cases covering all parameters:

```bash
# Run all tests
pytest tangle/test_perplx_client.py -v

# Run specific test class
pytest tangle/test_perplx_client.py::TestModelConfigParameters -v

# Run with coverage
pytest tangle/test_perplx_client.py --cov=tangle
```

### Test Coverage

- **ModelConfig Parameters** (28 tests) - All 13 parameters tested individually and in combinations
- **SearchFilter Parameters** (26 tests) - Domain filtering, date filtering, validation
- **ModelInput Parameters** (16 tests) - Input validation, prompt handling, attachments
- **Parameter Combinations** (7 tests) - How parameters interact with each other
- **Integration Tests** (17 tests) - Full workflow tests

## Development

### Setup Development Environment

```bash
# Create virtual environment
python3 -m venv perplxenv
source perplxenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Run type checks
make type-check
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

### Version 0.2.0 (Current)
- Core `PerplexityClient` with flexible configuration
- `ModelConfig` with 13 parameters for fine-grained control
- `SearchFilter` high-level abstraction for domain and date filtering
- `ModelInput` for multi-modal inputs (text, images, PDFs)
- Pydantic-based structured output with JSON schema validation
- Comprehensive test suite with 94+ parameter tests
- Specialized applications: Disease QA, Research Finder, Daily Knowledge Bot, Fact Checker
- Medicine lookup and DrugBank integration
- Image and PDF processing utilities

### Version 0.1.0 (Initial Release)
- Core text client with query, reasoning, research, and chat
- Advanced search with 30+ configuration parameters
- Domain discovery and filtering
- PDF processing capabilities
- Image processing support
- Medicine/drug lookup system
- CLI tools for all major features
