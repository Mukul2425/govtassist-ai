from pydantic import BaseModel, ConfigDict, Field


class EligibilityRuleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field: str
    operator: str
    value: object
    is_required: bool = True
    description: str | None = None


class SchemeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    short_description: str
    government_level: str
    ministry: str | None
    category: str
    applicable_states: list[str]
    benefits: list[str]
    application_url: str | None
    official_source_url: str


class SchemeDetail(SchemeSummary):
    full_description: str
    required_documents: list[str]
    application_process: str
    eligibility_rules: list[EligibilityRuleSchema]
    verified_at: object | None = None
    updated_at: object | None = None


class SchemeListResponse(BaseModel):
    schemes: list[SchemeSummary]
    total: int
    page: int
    page_size: int
