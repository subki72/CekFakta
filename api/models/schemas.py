"""
Pydantic schemas for request and response validation.

All API inputs and outputs are validated against these schemas.
FastAPI automatically generates OpenAPI/Swagger documentation from them.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# --- Enums ---

class InputType(str, Enum):
    TEXT = "TEXT"
    URL = "URL"
    IMAGE = "IMAGE"


class Label(str, Enum):
    OBJEKTIF = "OBJEKTIF"
    CENDERUNG_BIAS = "CENDERUNG_BIAS"
    SANGAT_MANIPULATIF = "SANGAT_MANIPULATIF"


# --- Request Schemas ---

class AnalyzeTextRequest(BaseModel):
    """Request body for text or URL analysis."""
    input_type: InputType = Field(
        default=InputType.TEXT,
        description="Input type: TEXT, URL, or IMAGE",
    )
    raw_input: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Narration text, article URL, or image base64 string",
    )


class VoteRequest(BaseModel):
    """Request body for submitting a community vote."""
    is_agree: bool = Field(
        ...,
        description="True = Agree with AI analysis, False = Disagree",
    )


class CommentRequest(BaseModel):
    """Request body for adding a community comment."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Comment content (maximum 2000 characters)",
    )


# --- Response Schemas ---

class AnalysisResult(BaseModel):
    """Objectivity analysis result."""
    analysis_id: str
    id: str | None = None
    input_type: InputType
    extracted_text: str
    detected_language: str
    score: int = Field(ge=0, le=100)
    label: Label
    reasoning: str
    highlighted_issues: list[str] = []
    buzzer_indicators: list[str] = []
    created_at: datetime


class AnalysisDetail(AnalysisResult):
    """Detailed analysis result with community interaction data."""
    vote_agree: int = 0
    vote_disagree: int = 0
    user_vote: bool | None = None
    comments: list[CommentOut] = []


class CommentOut(BaseModel):
    """Comment data returned to client."""
    id: str
    user_name: str
    content: str
    created_at: datetime


class TrendingTopic(BaseModel):
    """Trending topic item in dashboard."""
    topic: str
    average_score: float
    total_analyzed: int
    label_distribution: dict[str, int] = {}


class VoteOut(BaseModel):
    """Aggregate vote count returned after a user votes."""
    vote_agree: int
    vote_disagree: int
    user_vote: bool


# --- Generic API Response Wrapper ---

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard generic API response wrapper."""
    success: bool = True
    data: T | None = None
    message: str | None = None


class APIError(BaseModel):
    """Standard API error response."""
    success: bool = False
    error: str
    code: str


# Resolve forward reference for AnalysisDetail
AnalysisDetail.model_rebuild()

