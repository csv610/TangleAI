"""Generate markdown prompts from Pydantic BaseModels"""

from pydantic import BaseModel
from typing import Type, get_origin, get_args


def model_to_markdown_structure(model: Type[BaseModel], level: int = 2) -> str:
    """Convert a Pydantic model to markdown structure with field descriptions."""
    lines = []

    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation
        desc = field_info.description or ""
        origin = get_origin(field_type)

        if origin is list:
            # Handle List[T]
            args = get_args(field_type)
            inner_type = args[0] if args else None

            if inner_type and hasattr(inner_type, 'model_fields'):
                # List of models
                lines.append(f"{'#' * level} {field_name}: `List[{inner_type.__name__}]`\n")
                lines.append(f"{desc}\n")
                nested = model_to_markdown_structure(inner_type, level + 1)
                lines.append(nested)
            else:
                # List of primitives
                type_name = getattr(inner_type, '__name__', str(inner_type))
                lines.append(f"{'#' * level} {field_name}: `List[{type_name}]`\n")
                lines.append(f"{desc}\n")

        elif hasattr(field_type, 'model_fields'):
            # Nested model
            lines.append(f"{'#' * level} {field_name}: `{field_type.__name__}`\n")
            lines.append(f"{desc}\n")
            nested = model_to_markdown_structure(field_type, level + 1)
            lines.append(nested)

        else:
            # Primitive types
            type_name = getattr(field_type, '__name__', str(field_type))
            lines.append(f"{'#' * level} {field_name}: `{type_name}`\n")
            lines.append(f"{desc}\n")

    return "\n".join(lines)


def generate_prompt(
    model: Type[BaseModel],
    task: str,
    instructions: str = "Return *only* valid JSON that fits this schema."
) -> str:
    """Generate a markdown formatted prompt from a BaseModel."""
    structure = model_to_markdown_structure(model)
    model_name = model.__name__

    return f"""# Generate a Detailed {model_name}

Generate a detailed {model_name.lower()} strictly following this Pydantic model structure.

## Schema

{structure}

## Task

{task}

## Instructions

{instructions}"""
