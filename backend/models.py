"""
Pydantic Models — Request/response schemas for the pseudonymization API.

Clean separation between the API layer and the internal agent/processing logic.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Internal models (used by the agent/pseudonymizer layer)
# ---------------------------------------------------------------------------

class DetectedEntity(BaseModel):
    """A single PII entity detected in the document."""
    original_text: str = Field(description="Exact text as it appears in the document")
    start: int = Field(description="Character start index, 0-based")
    end: int = Field(description="Character end index, exclusive")
    entity_type: str = Field(description="Category label (e.g., FIRST_NAME, EMAIL, SSN)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    instance_id: str = Field(description="Consistent label like FIRST_NAME_1")


class AgentResponse(BaseModel):
    """Raw structured output from the LLM agent."""
    entities: list[DetectedEntity] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API request/response models
# ---------------------------------------------------------------------------

class PseudonymizeRequest(BaseModel):
    """Request body for POST /pseudonymize."""
    text: str = Field(
        min_length=1,
        max_length=50000,
        description="The document text to pseudonymize"
    )


class EntityInfo(BaseModel):
    """Per-entity information exposed in the API response."""
    original_text: str = Field(description="The original PII text (included for click-to-expand detail)")
    pseudonym: str = Field(description="The replacement label (e.g., [FIRST_NAME_1])")
    entity_type: str = Field(description="Category of PII")
    confidence: float = Field(ge=0.0, le=1.0)
    start: int = Field(description="Start position in the ORIGINAL text")
    end: int = Field(description="End position in the ORIGINAL text")
    pseudonym_start: int = Field(description="Start position in the PSEUDONYMIZED text")
    pseudonym_end: int = Field(description="End position in the PSEUDONYMIZED text")


class CategoryCount(BaseModel):
    """Count of entities per category for the summary breakdown."""
    category: str = Field(description="Human-readable category name")
    count: int = Field(ge=0)


class PseudonymizeResponse(BaseModel):
    """Response body for POST /pseudonymize."""
    pseudonymized_text: str = Field(description="The document with PII replaced by pseudonym labels")
    entities: list[EntityInfo] = Field(description="Per-entity detail for optional click-to-expand UI")
    trust_score: float = Field(ge=0.0, le=10.0, description="Trust score out of 10")
    category_breakdown: list[CategoryCount] = Field(description="Counts per entity category")
    summary: str = Field(description="Plain-language paragraph describing what was found")
    entity_count: int = Field(ge=0, description="Total number of entities detected")


class ErrorResponse(BaseModel):
    """Error response for API failures."""
    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    detail: str | None = Field(default=None, description="Additional detail for debugging")


class HealthResponse(BaseModel):
    """Response for GET /health."""
    status: str = "ok"
    llm_provider: str = Field(description="Currently configured LLM provider")
