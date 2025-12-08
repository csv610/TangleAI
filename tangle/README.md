# Perplexity Client

A Python client wrapper for the Perplexity API that provides high-level abstractions for easy integration with search filtering, image/PDF support, and structured outputs.

## Features

- **High-level Search Filtering**: Intuitive `SearchFilter` class for constraining search results by domains, dates, and recency
- **Multi-media Support**: Handle images and PDFs alongside text queries
- **Structured Output**: Built-in support for Pydantic models for structured responses
- **Clean API**: Simple, user-friendly interface hiding low-level complexity

## Installation

```bash
pip install perplexity-sdk pydantic
```

Set the API key as an environment variable:
```bash
export PERPLEXITY_API_KEY="your-api-key"
```

## Quick Start

### Basic Usage

```python
from perplx_client import PerplexityClient
from config import ModelInput

client = PerplexityClient()

model_input = ModelInput(
    user_prompt="Tell me about renewable energy"
)

response = client.generate_content(model_input)
print(response.choices[0].message.content)
```

### Using SearchFilter

Filter search results by domains, dates, and recency without worrying about low-level API details:

```python
from perplx_client import PerplexityClient
from config import ModelInput, SearchFilter

client = PerplexityClient()

# Filter by allowed domains and recency
search_filter = SearchFilter(
    allowed_domains=["nasa.gov", "wikipedia.org", "arxiv.org"],
    recency="week"
)

model_input = ModelInput(
    user_prompt="What are the latest discoveries in space exploration?"
)

response = client.generate_content(model_input, search_filter=search_filter)
```

### Excluding Domains

```python
# Exclude low-quality sources
search_filter = SearchFilter(
    blocked_domains=["reddit.com", "pinterest.com", "quora.com"]
)

response = client.generate_content(model_input, search_filter=search_filter)
```

### Filtering by Publication Date

```python
# Find articles published in a specific date range
search_filter = SearchFilter(
    published_after="1/1/2025",
    published_before="3/1/2025"
)

response = client.generate_content(model_input, search_filter=search_filter)
```

### Filtering by Last Updated Date

```python
# Find recently updated content
search_filter = SearchFilter(
    updated_after="1/1/2025",
    updated_before="3/1/2025"
)

response = client.generate_content(model_input, search_filter=search_filter)
```

## SearchFilter Parameters

### Domain Filtering

- **`allowed_domains`** - Whitelist mode: Only search these domains/URLs (max 20)
  - Examples: `["nasa.gov", "wikipedia.org", "https://arxiv.org/"]`
  - Note: Test URLs for accessibility before production use

- **`blocked_domains`** - Blacklist mode: Exclude these domains/URLs (max 20)
  - Examples: `["reddit.com", "pinterest.com"]`
  - Cannot be combined with `allowed_domains`

### Time Filtering (Choose One Approach)

- **`recency`** - Quick filtering by relative time periods
  - Values: `"day"`, `"week"`, `"month"`, `"year"`
  - Cannot be combined with specific date filters

- **`published_after`** / **`published_before`** - Filter by publication date
  - Format: `"m/d/Y"` (e.g., `"3/1/2025"` or `"03/01/2025"`)
  - Can be used together to define a date range

- **`updated_after`** / **`updated_before`** - Filter by last updated date
  - Format: `"m/d/Y"` (e.g., `"3/1/2025"`)
  - Can be used together to define a date range
  - Can be combined with publication date filters

## Advanced Usage

### With Custom Model Configuration

```python
from config import ModelConfig, SearchFilter

config = ModelConfig(
    model="sonar-pro",
    max_tokens=2048,
    temperature=0.5
)

search_filter = SearchFilter(
    allowed_domains=["nature.com", "science.org"],
    recency="month"
)

response = client.generate_content(model_input, config=config, search_filter=search_filter)
```

### With Images

```python
model_input = ModelInput(
    user_prompt="What's in this image?",
    image_path="/path/to/image.jpg"
)

response = client.generate_content(model_input)
```

### With PDFs

```python
model_input = ModelInput(
    user_prompt="Summarize this document",
    pdf_path="/path/to/document.pdf"
)

response = client.generate_content(model_input)
```

### With Structured Output

```python
from pydantic import BaseModel
from typing import List

class ResearchSummary(BaseModel):
    title: str
    key_findings: List[str]
    sources: List[str]

model_input = ModelInput(
    user_prompt="Research renewable energy trends",
    response_model=ResearchSummary
)

response = client.generate_content(model_input)
# Response will be automatically parsed into ResearchSummary
```

## SearchFilter Validation

The `SearchFilter` class automatically validates configurations:

- ❌ Cannot use both `allowed_domains` and `blocked_domains` simultaneously (choose allowlist or denylist mode)
- ❌ Cannot combine `recency` with specific date filters
- ❌ Maximum 20 domains/URLs per filter
- ❌ `recency` must be one of: `"day"`, `"week"`, `"month"`, `"year"`

Invalid configurations raise `ValueError` with clear error messages.

## Best Practices

1. **Domain Filtering**
   - Use simple domain names (e.g., `example.com`) for broad filtering
   - Use complete URLs (e.g., `https://example.com/page`) for specific page targeting
   - Using a main domain (e.g., `nytimes.com`) will filter all subdomains

2. **Time Filtering**
   - Use `recency` for convenience when you need recent content (e.g., "past week")
   - Use specific date filters for precise control over time ranges
   - Test URL accessibility before using them in allowlist mode (blocked or auth-required URLs won't return results)

3. **Performance**
   - Domain filters may slightly increase response time
   - Overly restrictive filters might reduce result quality
   - Use fewer, more targeted entries for best results


## Architecture

- **`SearchFilter`** - High-level, user-friendly search constraint interface for filtering domains, dates, and recency
- **`ModelConfig`** - Model behavior parameters (temperature, tokens, penalties, search mode, etc.)
- **`ModelInput`** - Input parameters (prompt, images, PDFs, system prompt)
- **`PerplexityClient`** - Main client class integrating all components
