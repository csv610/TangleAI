# Pydantic Utilities & Prompt Generation

Clean utilities for working with Pydantic models and generating structured prompts.

## Files

### Core Utilities

**`pydantic_utils.py`**
- `display_model()` - Display Pydantic models with nested structure and indentation
- `get_field_descriptions()` - Generate readable field descriptions including list type detection
- `build_display_string()` - Join multiple strings with separator

**`simple_prompt_gen.py`**
- `generate_prompt()` - Generate markdown formatted prompts from any BaseModel
- `model_to_markdown_structure()` - Convert BaseModel to readable markdown structure

**`markdown_model_doc.py`**
- `model_to_markdown()` - Generate complete markdown documentation from BaseModels

### Examples

**`city_info.py`**
- Fetches city information from Perplexity API
- Uses nested models with field descriptions
- Uses `get_field_descriptions()` to dynamically generate prompts

## Quick Start

### Generate a Prompt from a BaseModel

```python
from pydantic import BaseModel, Field
from typing import List
from simple_prompt_gen import generate_prompt

class Section(BaseModel):
    title: str = Field(..., description="Section heading")
    content: str = Field(..., description="Section content")

class Article(BaseModel):
    topic: str = Field(..., description="Article topic")
    sections: List[Section] = Field(..., description="Article sections")

# Generate markdown prompt
prompt = generate_prompt(Article, "Write about Machine Learning")
print(prompt)
```

Output:
```markdown
# Generate a Detailed Article

Generate a detailed article strictly following this Pydantic model structure.

## Schema

## topic: `str`

Article topic

## sections: `List[Section]`

Article sections

### title: `str`

Section heading

### content: `str`

Section content

## Task

Write about Machine Learning

## Instructions

Return *only* valid JSON that fits this schema.
```

### Display a Model Instance

```python
from pydantic_utils import display_model

article = Article(
    topic="Machine Learning",
    sections=[
        Section(title="Introduction", content="ML is..."),
        Section(title="Applications", content="ML is used for...")
    ]
)

display_model(article, title_field="topic")
```

## Features

✅ **Automatic nested model detection** - Handles List[Model] and Optional[List[Model]]
✅ **Field descriptions included** - From Pydantic Field() definitions
✅ **Clean markdown format** - Ready for API prompts
✅ **Recursive structure support** - Handles deeply nested models
✅ **Type inference** - Automatically detects List, Optional, and nested models

## Best Practices

1. **Add clear descriptions** to all fields using `Field(..., description="...")`
2. **Use specific types** - `List[Model]` instead of `List[dict]`
3. **Nest models** instead of flattening structure
4. **Skip internal fields** - Use `skip_fields` parameter when needed

## Example: Medical Article

```python
from pydantic import BaseModel, Field
from typing import List
from simple_prompt_gen import generate_prompt

class Section(BaseModel):
    title: str = Field(..., description="A clear, concise heading for this section")
    content: str = Field(..., description="Detailed explanation with 2-4 paragraphs")

class MedicalArticle(BaseModel):
    topic: str = Field(..., description="Main medical subject")
    sections: List[Section] = Field(..., description="Article sections")

prompt = generate_prompt(MedicalArticle, "Iron Deficiency Anemia in Children")
print(prompt)
```

This generates a clean, structured prompt ready to send to LLMs!
