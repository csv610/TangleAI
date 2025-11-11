"""Test nested Pydantic models with lists - comprehensive test suite"""

from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic_utils import display_model


# Define models for list testing
class Tag(BaseModel):
    name: str
    color: Optional[str] = None


class Comment(BaseModel):
    author: str
    text: str
    likes: int = Field(default=0, json_schema_extra={"formatter": lambda v: f"{v} likes"})


class Post(BaseModel):
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    comments: List[Comment] = Field(default_factory=list)
    likes: int = Field(default=0)


class Blog(BaseModel):
    name: str
    author: str
    posts: List[Post] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: str
    tags: List[Tag] = Field(default_factory=list)
    team_members: List[str] = Field(default_factory=list)


class Organization(BaseModel):
    name: str
    projects: List[Project] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)


class Review(BaseModel):
    rating: int = Field(..., json_schema_extra={"formatter": lambda v: f"{v}/5 stars"})
    text: str


class Product(BaseModel):
    name: str
    price: float = Field(..., json_schema_extra={"formatter": lambda v: f"${v:.2f}"})
    reviews: List[Review] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class Store(BaseModel):
    name: str
    products: List[Product] = Field(default_factory=list)


# Test cases
def test_list_of_primitives():
    """Test list of primitive values in nested model"""
    print("\n" + "="*60)
    print("TEST 1: List of Primitives in Nested Model")
    print("="*60)

    post = Post(
        title="Python Tips",
        content="Top 10 Python tips for developers",
        tags=["python", "programming", "tips", "tutorial"],
        likes=42
    )

    display_model(post)


def test_list_of_nested_models():
    """Test list of nested BaseModel instances"""
    print("\n" + "="*60)
    print("TEST 2: List of Nested Models (Comments)")
    print("="*60)

    post = Post(
        title="Great Article",
        content="This is an amazing article",
        tags=["blog", "featured"],
        comments=[
            Comment(author="Alice", text="Love this!", likes=5),
            Comment(author="Bob", text="Very informative", likes=8),
            Comment(author="Charlie", text="Thanks for sharing", likes=3)
        ],
        likes=25
    )

    display_model(post)


def test_deeply_nested_lists():
    """Test deeply nested models with lists at multiple levels"""
    print("\n" + "="*60)
    print("TEST 3: Deeply Nested Lists (Blog -> Posts -> Comments)")
    print("="*60)

    blog = Blog(
        name="Tech Blog",
        author="Sarah Chen",
        posts=[
            Post(
                title="Getting Started with FastAPI",
                content="Learn FastAPI from scratch",
                tags=["fastapi", "python", "web"],
                comments=[
                    Comment(author="Dev1", text="Great tutorial!", likes=12),
                    Comment(author="Dev2", text="Clear explanation", likes=8)
                ],
                likes=45
            ),
            Post(
                title="Docker Best Practices",
                content="Tips for using Docker effectively",
                tags=["docker", "devops", "containers"],
                comments=[
                    Comment(author="OpsTeam", text="Exactly what we needed", likes=15)
                ],
                likes=30
            )
        ],
        categories=["Backend", "DevOps", "Tutorials"]
    )

    display_model(blog)


def test_list_of_models_with_formatter():
    """Test list of models where items have custom formatters"""
    print("\n" + "="*60)
    print("TEST 4: List of Models with Custom Formatters (Reviews)")
    print("="*60)

    product = Product(
        name="Laptop",
        price=999.99,
        tags=["electronics", "computers", "portable"],
        reviews=[
            Review(rating=5, text="Excellent build quality"),
            Review(rating=4, text="Good performance, bit heavy"),
            Review(rating=5, text="Worth the investment"),
            Review(rating=4, text="Battery life could be better")
        ]
    )

    display_model(product)


def test_store_with_multiple_products():
    """Test Store with list of Products"""
    print("\n" + "="*60)
    print("TEST 5: Store with Multiple Products (2-level nesting)")
    print("="*60)

    store = Store(
        name="TechMart",
        products=[
            Product(
                name="Keyboard",
                price=79.99,
                tags=["input", "mechanical"],
                reviews=[
                    Review(rating=5, text="Best keyboard ever"),
                    Review(rating=4, text="Comfortable but loud")
                ]
            ),
            Product(
                name="Mouse",
                price=49.99,
                tags=["input", "ergonomic"],
                reviews=[
                    Review(rating=5, text="Smooth tracking")
                ]
            )
        ]
    )

    display_model(store)


def test_organization_projects():
    """Test Organization with Projects containing Tag models"""
    print("\n" + "="*60)
    print("TEST 6: Organization with Projects and Tags")
    print("="*60)

    org = Organization(
        name="TechCorp Inc",
        projects=[
            Project(
                name="Mobile App",
                description="Cross-platform mobile application",
                tags=[
                    Tag(name="python", color="blue"),
                    Tag(name="react", color="cyan"),
                    Tag(name="mobile", color="green")
                ],
                team_members=["Alice", "Bob", "Charlie"]
            ),
            Project(
                name="Data Pipeline",
                description="ETL data processing system",
                tags=[
                    Tag(name="python", color="blue"),
                    Tag(name="data", color="orange"),
                    Tag(name="spark", color="red")
                ],
                team_members=["Dave", "Eve"]
            )
        ],
        departments=["Engineering", "QA", "DevOps"]
    )

    display_model(org)


def test_empty_lists():
    """Test models with empty lists"""
    print("\n" + "="*60)
    print("TEST 7: Empty Lists in Nested Models")
    print("="*60)

    post = Post(
        title="Pending Review",
        content="This post is still pending",
        tags=[],
        comments=[],
        likes=0
    )

    display_model(post)


def test_mixed_empty_and_populated_lists():
    """Test model with some empty and some populated lists"""
    print("\n" + "="*60)
    print("TEST 8: Mixed Empty and Populated Lists")
    print("="*60)

    blog = Blog(
        name="New Blog",
        author="John Doe",
        posts=[
            Post(
                title="First Post",
                content="My first blog post",
                tags=["first", "blog"],
                comments=[],
                likes=2
            )
        ],
        categories=[]
    )

    display_model(blog)


def test_list_with_single_item():
    """Test lists with just one item"""
    print("\n" + "="*60)
    print("TEST 9: Lists with Single Item")
    print("="*60)

    post = Post(
        title="Solo Comment Post",
        content="Post with single comment",
        tags=["single"],
        comments=[
            Comment(author="OnlyReader", text="Nice post!", likes=1)
        ],
        likes=5
    )

    display_model(post)


def test_deeply_nested_mixed_lists():
    """Test deeply nested with mix of primitive and model lists"""
    print("\n" + "="*60)
    print("TEST 10: Deeply Nested Mixed Lists")
    print("="*60)

    org = Organization(
        name="MultiLevel Corp",
        projects=[
            Project(
                name="Web Platform",
                description="Full-stack web application",
                tags=[
                    Tag(name="frontend", color="blue"),
                    Tag(name="backend", color="green"),
                    Tag(name="fullstack", color="purple")
                ],
                team_members=["Alice", "Bob", "Charlie", "Dave"]
            ),
            Project(
                name="Analytics",
                description="Data analytics platform",
                tags=[
                    Tag(name="data", color="orange")
                ],
                team_members=["Eve"]
            ),
            Project(
                name="Infrastructure",
                description="Cloud infrastructure setup",
                tags=[
                    Tag(name="devops", color="red"),
                    Tag(name="cloud", color="yellow")
                ],
                team_members=["Frank", "Grace"]
            )
        ],
        departments=["Engineering", "Operations", "Analytics", "DevOps"]
    )

    display_model(org)


def test_skip_fields_with_lists():
    """Test skip_fields parameter with lists"""
    print("\n" + "="*60)
    print("TEST 11: Skip Fields with Lists")
    print("="*60)

    post = Post(
        title="Skip Test Post",
        content="Testing skip_fields functionality",
        tags=["test", "skip", "fields"],
        comments=[
            Comment(author="Tester", text="Testing skip", likes=10),
            Comment(author="Another", text="Another test", likes=5)
        ],
        likes=20
    )

    print("Display with comments and likes skipped:")
    display_model(post, skip_fields=["comments", "likes"])


def test_large_list():
    """Test with larger list to see formatting"""
    print("\n" + "="*60)
    print("TEST 12: Large List of Nested Models")
    print("="*60)

    comments = [
        Comment(author=f"User{i}", text=f"Comment {i}", likes=i*2)
        for i in range(5)
    ]

    post = Post(
        title="Popular Post",
        content="This post went viral!",
        tags=["viral", "trending", "popular", "featured"],
        comments=comments,
        likes=1000
    )

    display_model(post)


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# NESTED MODELS WITH LISTS - COMPREHENSIVE TEST SUITE")
    print("#"*60)

    test_list_of_primitives()
    test_list_of_nested_models()
    test_deeply_nested_lists()
    test_list_of_models_with_formatter()
    test_store_with_multiple_products()
    test_organization_projects()
    test_empty_lists()
    test_mixed_empty_and_populated_lists()
    test_list_with_single_item()
    test_deeply_nested_mixed_lists()
    test_skip_fields_with_lists()
    test_large_list()

    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETED")
    print("#"*60 + "\n")
