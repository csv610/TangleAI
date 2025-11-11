from typing import List, Optional
from pydantic import BaseModel, Field


class ConceptDefinition(BaseModel):
    """Schema for defining a concept with explanation."""
    name: str = Field(..., description="Name of the concept")
    definition: str = Field(..., description="Clear definition of the concept")
    relevance: str = Field(..., description="Why this concept is relevant")


class ChapterQuestion(BaseModel):
    """Schema for chapter discussion questions."""
    question: str = Field(..., description="The question to consider")
    category: str = Field(
        default="general",
        description="Category of question (e.g., 'comprehension', 'application', 'critical_thinking')"
    )
    difficulty: str = Field(
        default="medium",
        description="Difficulty level (easy, medium, hard)"
    )


class LearningPoint(BaseModel):
    """Schema for individual learning points."""
    title: str = Field(..., description="Title of the learning point")
    description: str = Field(..., description="Detailed description")
    importance: str = Field(
        default="medium",
        description="Importance level (low, medium, high)"
    )


class PracticalApplication(BaseModel):
    """Schema for practical applications of concepts."""
    title: str = Field(..., description="Title of the application")
    description: str = Field(..., description="How to apply this in practice")
    domain: str = Field(..., description="Domain or field of application")
    difficulty: str = Field(
        default="medium",
        description="Difficulty to implement (beginner, intermediate, advanced)"
    )


class ChapterConnection(BaseModel):
    """Schema for connections between chapters."""
    related_chapter: str = Field(..., description="Title or number of related chapter")
    connection_type: str = Field(
        ...,
        description="Type of connection (prerequisite, builds_on, related_to, expands_on)"
    )
    description: str = Field(..., description="How the chapters are connected")


class BaseChapter(BaseModel):
    """Base schema for chapter analysis with comprehensive structure."""
    chapter_number: int = Field(..., description="Chapter number in the book")
    chapter_title: str = Field(..., description="Title of the chapter")
    duration_estimate: Optional[str] = Field(
        default=None,
        description="Estimated time to study this chapter (e.g., '2-3 hours')"
    )
    summary: str = Field(..., description="Comprehensive summary of the chapter")

    # Core Content
    key_concepts: List[ConceptDefinition] = Field(
        default_factory=list,
        description="Key concepts introduced in this chapter"
    )
    main_topics: List[str] = Field(
        default_factory=list,
        description="Main topics covered"
    )
    learning_points: List[LearningPoint] = Field(
        default_factory=list,
        description="Key learning points with importance levels"
    )

    # Practical Value
    practical_applications: List[PracticalApplication] = Field(
        default_factory=list,
        description="How to apply concepts from this chapter"
    )

    # Engagement
    questions_to_consider: List[ChapterQuestion] = Field(
        default_factory=list,
        description="Discussion and reflection questions"
    )

    # Relationships
    connections_to_other_chapters: List[ChapterConnection] = Field(
        default_factory=list,
        description="How this chapter connects to others"
    )

    # Prerequisites and Next Steps
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Knowledge or chapters you should understand first"
    )
    builds_toward: List[str] = Field(
        default_factory=list,
        description="Chapters or concepts this chapter prepares you for"
    )

    # Assessment
    key_definitions: List[str] = Field(
        default_factory=list,
        description="Important terms to remember from this chapter"
    )
    common_misconceptions: List[str] = Field(
        default_factory=list,
        description="Common misunderstandings about topics in this chapter"
    )

    # Meta
    difficulty_level: str = Field(
        default="medium",
        description="Difficulty level (beginner, intermediate, advanced)"
    )
    chapter_type: str = Field(
        default="standard",
        description="Type of chapter (standard, case_study, practical_lab, review, conclusion)"
    )


class EnhancedChapter(BaseChapter):
    """Extended chapter schema with additional metadata and resources."""

    # Resources
    recommended_resources: List[str] = Field(
        default_factory=list,
        description="Books, articles, or websites for deeper learning"
    )
    practice_exercises: List[str] = Field(
        default_factory=list,
        description="Suggested exercises to practice concepts"
    )

    # Engagement Metrics
    estimated_readability: str = Field(
        default="moderate",
        description="How readable/accessible the chapter is"
    )
    key_figures_or_diagrams: List[str] = Field(
        default_factory=list,
        description="Important figures, diagrams, or visual elements"
    )

    # Learning Objectives
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="What you should be able to do after this chapter"
    )

    # Context
    historical_context: Optional[str] = Field(
        default=None,
        description="Historical background or development of concepts"
    )
