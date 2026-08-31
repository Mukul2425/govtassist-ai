from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.profile import UserProfile


class EligibilityStatus(str, Enum):
    LIKELY_ELIGIBLE = "likely_eligible"
    POSSIBLY_ELIGIBLE = "possibly_eligible"
    NOT_ELIGIBLE = "not_eligible"
    INSUFFICIENT_INFO = "insufficient_info"


class RuleEvaluationResult(BaseModel):
    field: str
    operator: str
    expected: Any
    actual: Any | None
    passed: bool
    is_required: bool
    description: str | None = None


class EligibilityResult(BaseModel):
    scheme_id: str
    scheme_name: str
    eligibility_status: EligibilityStatus
    matched_rules: int
    failed_rules: int
    total_rules: int
    missing_information: list[str]
    rule_details: list[RuleEvaluationResult]
    score: float = Field(ge=0, le=100)


class SchemeRecommendation(BaseModel):
    scheme_id: str
    scheme_name: str
    short_description: str
    eligibility_status: EligibilityStatus
    eligibility_score: float
    why_eligible: str
    benefits: list[str]
    required_documents: list[str]
    application_process: str
    application_url: str | None
    official_source_url: str
    missing_information: list[str]
    retrieved_context: list[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=2000)
    profile: UserProfile | None = None
    max_results: int = Field(10, ge=1, le=25)


class RecommendationResponse(BaseModel):
    session_id: str
    query: str
    extracted_profile: UserProfile
    recommendations: list[SchemeRecommendation]
    follow_up_questions: list[str]
    disclaimer: str
    response_summary: str
