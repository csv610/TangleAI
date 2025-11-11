"""Generate markdown documentation from Pydantic BaseModel"""

from pydantic import BaseModel
from typing import List, Optional, get_origin, get_args, Type
import inspect


def is_list_field(field_type) -> bool:
    """Check if a field type is a List or Optional[List]."""
    from typing import Union
    origin = get_origin(field_type)

    if origin is list:
        return True

    if origin is Union:
        args = get_args(field_type)
        for arg in args:
            if get_origin(arg) is list:
                return True

    return False


def is_pydantic_model(field_type) -> bool:
    """Check if a field type is a Pydantic BaseModel."""
    try:
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            return True
    except TypeError:
        pass

    # Handle Optional[Model]
    origin = get_origin(field_type)
    if origin is not None:
        args = get_args(field_type)
        for arg in args:
            try:
                if isinstance(arg, type) and issubclass(arg, BaseModel):
                    return True
            except TypeError:
                pass

    return False


def get_inner_type(field_type):
    """Get the inner type from List[T] or Optional[T]."""
    args = get_args(field_type)
    if args:
        return args[0]
    return None


def get_type_name(field_type) -> str:
    """Get a readable type name."""
    origin = get_origin(field_type)

    if origin is list:
        inner = get_args(field_type)[0] if get_args(field_type) else None
        if inner:
            if isinstance(inner, type) and issubclass(inner, BaseModel):
                return f"List[{inner.__name__}]"
            elif isinstance(inner, type):
                return f"List[{inner.__name__}]"
            else:
                return f"List[{inner}]"
        return "List"

    if isinstance(field_type, type):
        return field_type.__name__

    return str(field_type)


def model_to_markdown(model_class: Type[BaseModel], indent: int = 0) -> str:
    """
    Generate markdown documentation for a Pydantic model.

    Args:
        model_class: Pydantic model class to document
        indent: Indentation level for nested models

    Returns:
        Markdown string describing the model
    """
    indent_str = "  " * indent
    md = ""

    # Model header
    md += f"{'#' * (2 + indent)} {model_class.__name__}\n\n"

    # Model docstring if available
    if model_class.__doc__:
        md += f"{model_class.__doc__.strip()}\n\n"

    # Fields table
    md += "| Field | Type | Description |\n"
    md += "|-------|------|-------------|\n"

    for field_name, field_info in model_class.model_fields.items():
        field_type = field_info.annotation
        type_name = get_type_name(field_type)

        # Get description from field
        description = field_info.description or ""

        md += f"| `{field_name}` | `{type_name}` | {description} |\n"

    md += "\n"

    # Nested models
    for field_name, field_info in model_class.model_fields.items():
        field_type = field_info.annotation

        # Handle List[Model]
        if is_list_field(field_type):
            inner_type = get_inner_type(field_type)
            if is_pydantic_model(inner_type):
                md += model_to_markdown(inner_type, indent + 1)
        # Handle direct Model
        elif is_pydantic_model(field_type):
            md += model_to_markdown(field_type, indent + 1)

    return md


# Test with examples
if __name__ == "__main__":
    # Example 1: Recipe
    class Ingredient(BaseModel):
        """An ingredient in a recipe"""
        name: str
        quantity: float
        unit: str = "grams"

    class Recipe(BaseModel):
        """A cooking recipe"""
        title: str
        ingredients: List[Ingredient]
        instructions: List[str]
        prep_time_minutes: int

    # Example 2: Book
    class Author(BaseModel):
        """Author information"""
        name: str
        email: str

    class Chapter(BaseModel):
        """A chapter in a book"""
        title: str
        pages: int

    class Book(BaseModel):
        """A book with chapters"""
        title: str
        author: Author
        chapters: List[Chapter]
        genres: List[str]

    # Example 3: Product with Reviews
    class Review(BaseModel):
        """Customer review"""
        author: str
        rating: int
        text: str

    class Product(BaseModel):
        """Product information"""
        name: str
        price: float
        reviews: List[Review]
        features: List[str]

    # Generate markdown
    print("=" * 70)
    print("RECIPE MODEL DOCUMENTATION")
    print("=" * 70)
    print(model_to_markdown(Recipe))

    print("\n" + "=" * 70)
    print("BOOK MODEL DOCUMENTATION")
    print("=" * 70)
    print(model_to_markdown(Book))

    print("\n" + "=" * 70)
    print("PRODUCT MODEL DOCUMENTATION")
    print("=" * 70)
    print(model_to_markdown(Product))
