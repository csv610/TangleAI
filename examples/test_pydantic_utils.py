"""Test suite for pydantic_utils with nested Pydantic models"""

from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic_utils import display_model, get_field_descriptions, build_display_string


# Define nested Pydantic models
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str


class Contact(BaseModel):
    email: str
    phone: Optional[str] = None
    address: Optional[Address] = None


class Person(BaseModel):
    name: str = Field(..., description="Person's full name")
    age: int = Field(..., json_schema_extra={"formatter": lambda v: f"{v} years old"})
    salary: float = Field(..., json_schema_extra={"formatter": lambda v: f"${v:,.2f}"})
    tags: List[str] = Field(default_factory=list)
    contact: Optional[Contact] = None


class Company(BaseModel):
    name: str
    employees: List[Person] = Field(default_factory=list)
    founded_year: int


# Test cases
def test_simple_nested_model():
    """Test display_model with a simple nested structure"""
    print("\n" + "="*60)
    print("TEST 1: Simple Nested Model (Person with Contact)")
    print("="*60)

    address = Address(
        street="123 Main St",
        city="San Francisco",
        state="CA",
        zip_code="94102"
    )

    contact = Contact(
        email="john@example.com",
        phone="555-1234",
        address=address
    )

    person = Person(
        name="John Doe",
        age=30,
        salary=75000.50,
        tags=["python", "ml", "devops"],
        contact=contact
    )

    display_model(person)


def test_nested_model_with_skip_fields():
    """Test display_model with skip_fields on nested model"""
    print("\n" + "="*60)
    print("TEST 2: Nested Model with Skip Fields")
    print("="*60)

    person = Person(
        name="Jane Smith",
        age=28,
        salary=85000.00,
        tags=["frontend", "react", "typescript"],
        contact=Contact(
            email="jane@example.com",
            phone="555-5678"
        )
    )

    display_model(person, skip_fields=["age", "tags"])


def test_nested_model_with_title():
    """Test display_model with title_field on nested model"""
    print("\n" + "="*60)
    print("TEST 3: Nested Model with Title Field")
    print("="*60)

    person = Person(
        name="Bob Johnson",
        age=35,
        salary=95000.75,
        tags=["backend", "golang", "kubernetes"],
        contact=Contact(email="bob@example.com")
    )

    display_model(person, title_field="name")


def test_multiple_level_nesting():
    """Test with deeply nested structures"""
    print("\n" + "="*60)
    print("TEST 4: Multiple Level Nesting (Company -> Employees -> Contact -> Address)")
    print("="*60)

    employee1 = Person(
        name="Alice",
        age=32,
        salary=90000.00,
        tags=["senior", "python"],
        contact=Contact(
            email="alice@company.com",
            phone="555-0001",
            address=Address(
                street="456 Oak Ave",
                city="New York",
                state="NY",
                zip_code="10001"
            )
        )
    )

    employee2 = Person(
        name="Charlie",
        age=26,
        salary=65000.00,
        tags=["junior", "javascript"],
        contact=Contact(
            email="charlie@company.com",
            phone="555-0002"
        )
    )

    company = Company(
        name="TechCorp",
        employees=[employee1, employee2],
        founded_year=2015
    )

    display_model(company)
    print("\nEmployee 1 Details:")
    display_model(employee1, skip_fields=["tags"])
    print("\nEmployee 2 Details:")
    display_model(employee2, skip_fields=["tags"])


def test_get_field_descriptions():
    """Test get_field_descriptions with nested models"""
    print("\n" + "="*60)
    print("TEST 5: Field Descriptions")
    print("="*60)

    print("\nPerson fields:")
    print(get_field_descriptions(Person))

    print("\nContact fields:")
    print(get_field_descriptions(Contact))

    print("\nAddress fields:")
    print(get_field_descriptions(Address))

    print("\nCompany fields:")
    print(get_field_descriptions(Company))


def test_build_display_string():
    """Test build_display_string utility"""
    print("\n" + "="*60)
    print("TEST 6: Build Display String")
    print("="*60)

    parts1 = ["Python", "Go", "JavaScript", "Rust"]
    print(f"Languages: {build_display_string(parts1)}")

    parts2 = ["Alice", "", "Bob", "", "Charlie"]
    print(f"Names (skip empty): {build_display_string(parts2, skip_empty=True)}")
    print(f"Names (include empty): {build_display_string(parts2, skip_empty=False)}")

    parts3 = ["2024", "Q1", "Report"]
    print(f"Report: {build_display_string(parts3, separator=' - ')}")


def test_nested_model_with_none_values():
    """Test display_model with None values in nested models"""
    print("\n" + "="*60)
    print("TEST 7: Nested Model with None Values")
    print("="*60)

    person = Person(
        name="Eve Wilson",
        age=29,
        salary=72000.00,
        contact=Contact(
            email="eve@example.com",
            phone=None,
            address=None
        )
    )

    display_model(person)


def test_nested_model_with_empty_lists():
    """Test display_model with empty lists in nested models"""
    print("\n" + "="*60)
    print("TEST 8: Nested Model with Empty Lists")
    print("="*60)

    person = Person(
        name="Frank Brown",
        age=31,
        salary=80000.00,
        tags=[],
        contact=Contact(email="frank@example.com")
    )

    display_model(person)


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# PYDANTIC UTILS TEST SUITE - NESTED MODELS")
    print("#"*60)

    test_simple_nested_model()
    test_nested_model_with_skip_fields()
    test_nested_model_with_title()
    test_multiple_level_nesting()
    test_get_field_descriptions()
    test_build_display_string()
    test_nested_model_with_none_values()
    test_nested_model_with_empty_lists()

    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETED")
    print("#"*60 + "\n")
