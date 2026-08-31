from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EducationLevel(str, Enum):
    BELOW_10TH = "below_10th"
    CLASS_10 = "class_10"
    CLASS_12 = "class_12"
    GRADUATE = "graduate"
    POST_GRADUATE = "post_graduate"
    PHD = "phd"
    DIPLOMA = "diploma"
    ITI = "iti"


class OccupationType(str, Enum):
    STUDENT = "student"
    FARMER = "farmer"
    SELF_EMPLOYED = "self_employed"
    SALARIED = "salaried"
    UNEMPLOYED = "unemployed"
    HOMEMAKER = "homemaker"
    RETIRED = "retired"
    BUSINESS = "business"
    LABORER = "laborer"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class UserProfile(BaseModel):
    age: int | None = Field(None, ge=0, le=120)
    state: str | None = None
    education: EducationLevel | str | None = None
    occupation: OccupationType | str | None = None
    annual_family_income: int | None = Field(None, ge=0)
    gender: Gender | str | None = None
    caste_category: str | None = Field(None, description="SC/ST/OBC/General/EWS")
    is_disabled: bool | None = None
    is_bpl: bool | None = Field(None, description="Below Poverty Line card holder")
    marital_status: str | None = None
    has_land: bool | None = None
    land_area_acres: float | None = Field(None, ge=0)
    is_woman: bool | None = None
    is_minority: bool | None = None
    district: str | None = None
    additional_info: dict[str, Any] = Field(default_factory=dict)

    @field_validator("state")
    @classmethod
    def normalize_state(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().title()

    @field_validator("education", "occupation", "gender", mode="before")
    @classmethod
    def normalize_enum(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower().strip().replace(" ", "_")
        return v

    def to_rule_context(self) -> dict[str, Any]:
        ctx: dict[str, Any] = {}
        for field_name, value in self.model_dump(exclude={"additional_info"}).items():
            if value is not None:
                ctx[field_name] = value
        ctx.update(self.additional_info)
        if self.age is not None and self.is_woman is None and self.gender == "female":
            ctx["is_woman"] = True
        return ctx

    def missing_fields(self, required: list[str]) -> list[str]:
        ctx = self.to_rule_context()
        return [f for f in required if f not in ctx or ctx[f] is None]


class ProfileExtractionRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=2000)


class ProfileExtractionResponse(BaseModel):
    profile: UserProfile
    confidence: float = Field(ge=0, le=1)
    extraction_notes: list[str] = Field(default_factory=list)
