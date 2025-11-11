"""Utility functions for working with Pydantic models"""

from typing import List, Type, Optional, Union, get_origin, get_args
from pydantic import BaseModel


def _is_pydantic_model(obj: any) -> bool:
    """Check if an object is a Pydantic BaseModel instance."""
    return isinstance(obj, BaseModel)


def _display_nested_model(
    model: BaseModel,
    indent: int = 0,
    skip_fields: Optional[List[str]] = None
) -> None:
    """
    Recursively display a Pydantic model with indentation for nested models.

    Args:
        model: Pydantic model instance to display
        indent: Number of spaces to indent (for nested models)
        skip_fields: List of field names to skip in output
    """
    skip_fields = skip_fields or []
    model_class = model.__class__
    indent_str = "  " * indent

    for field_name, field_info in model_class.model_fields.items():
        if field_name in skip_fields:
            continue

        value = getattr(model, field_name, None)
        if value is None:
            continue

        # Format field name for display
        display_name = field_name.replace('_', ' ').title()

        # Check if field has custom formatter in metadata
        formatter = None
        if field_info.json_schema_extra and isinstance(field_info.json_schema_extra, dict):
            formatter = field_info.json_schema_extra.get('formatter')

        # Handle different value types
        if isinstance(value, list):
            # Check if list contains BaseModel instances
            if value and _is_pydantic_model(value[0]):
                # Display list of nested models
                print(f"{indent_str}{display_name}:")
                for idx, item in enumerate(value):
                    print(f"{indent_str}  [{idx}]")
                    _display_nested_model(item, indent + 2, skip_fields=[])
            else:
                # Display list of primitives
                formatted_value = ', '.join(str(item) for item in value)
                print(f"{indent_str}{display_name}: {formatted_value}")
        elif _is_pydantic_model(value):
            # Recursively display nested model
            print(f"{indent_str}{display_name}:")
            _display_nested_model(value, indent + 1, skip_fields=[])
        elif formatter:
            formatted_value = formatter(value)
            print(f"{indent_str}{display_name}: {formatted_value}")
        else:
            formatted_value = str(value)
            print(f"{indent_str}{display_name}: {formatted_value}")


def display_model(
    model: BaseModel,
    skip_fields: Optional[List[str]] = None,
    title_field: Optional[str] = None,
    title_separator: str = ", "
) -> None:
    """
    Display a Pydantic model instance using metadata-driven formatting.

    Recursively displays nested Pydantic models with indentation.
    Fields can have custom formatters defined in json_schema_extra:
    Example: Field(..., json_schema_extra={"formatter": lambda v: f"{v:,}"})

    Args:
        model: Pydantic model instance to display
        skip_fields: List of field names to skip in output
        title_field: Field name to use as title header (printed separately)
        title_separator: Separator when joining title fields
    """
    skip_fields = skip_fields or []

    # Print title if specified
    if title_field:
        title_parts = []
        for field in title_field if isinstance(title_field, list) else [title_field]:
            value = getattr(model, field, None)
            if value is not None:
                title_parts.append(str(value))
        if title_parts:
            print(f"\n{title_separator.join(title_parts)}")

    # Display all fields (recursively handles nested models)
    _display_nested_model(model, indent=0, skip_fields=skip_fields)


def _is_list_field(field_type) -> bool:
    """Check if a field type is a List or Optional[List]."""
    origin = get_origin(field_type)

    # Direct List check
    if origin is list:
        return True

    # Check for Optional[List[...]] (which is Union[List[...], None])
    if origin is Union:
        args = get_args(field_type)
        # Optional[X] is Union[X, None], so check if first arg is List
        for arg in args:
            if get_origin(arg) is list:
                return True

    return False


def get_field_descriptions(
    model_class: Type[BaseModel],
    skip_fields: Optional[List[str]] = None
) -> str:
    """
    Generate readable field descriptions from a Pydantic model.

    List fields are formatted as "list of field_name".

    Args:
        model_class: Pydantic model class
        skip_fields: List of field names to exclude

    Returns:
        Comma-separated string of readable field names and list fields
    """
    skip_fields = skip_fields or []
    fields = []

    for field_name, field_info in model_class.model_fields.items():
        if field_name not in skip_fields:
            # Convert field_name to readable format
            readable_name = field_name.replace('_', ' ')

            # Check if field is a List type
            if _is_list_field(field_info.annotation):
                fields.append(f"list of {readable_name}")
            else:
                fields.append(readable_name)

    return ", ".join(fields) + "."


def build_display_string(
    parts: List[str],
    separator: str = ", ",
    skip_empty: bool = True
) -> str:
    """
    Build a display string by joining multiple parts.

    Args:
        parts: List of strings to join
        separator: String to use as separator
        skip_empty: If True, skip empty strings

    Returns:
        Joined string
    """
    if skip_empty:
        parts = [p for p in parts if p]
    return separator.join(parts)
