"""Recommendation ranking engine."""

from app.schemas.profile import UserProfile
from app.schemas.recommendation import EligibilityResult, EligibilityStatus


def rank_schemes(
    eligibility_results: list[EligibilityResult],
    profile: UserProfile,
    max_results: int = 10,
) -> list[EligibilityResult]:
    status_priority = {
        EligibilityStatus.LIKELY_ELIGIBLE: 4,
        EligibilityStatus.POSSIBLY_ELIGIBLE: 3,
        EligibilityStatus.INSUFFICIENT_INFO: 2,
        EligibilityStatus.NOT_ELIGIBLE: 1,
    }

    def sort_key(result: EligibilityResult) -> tuple[int, float, int]:
        geo_bonus = 0
        if profile.state and result.scheme_id:
            geo_bonus = 1
        return (
            status_priority.get(result.eligibility_status, 0),
            result.score,
            geo_bonus,
        )

    filtered = [
        r
        for r in eligibility_results
        if r.eligibility_status != EligibilityStatus.NOT_ELIGIBLE
    ]

    ranked = sorted(filtered, key=sort_key, reverse=True)
    return ranked[:max_results]


def generate_follow_up_questions(
    eligibility_results: list[EligibilityResult],
    profile: UserProfile,
    max_questions: int = 3,
) -> list[str]:
    field_questions = {
        "age": "What is your age?",
        "state": "Which state do you reside in?",
        "education": "What is your highest level of education?",
        "occupation": "What is your current occupation?",
        "annual_family_income": "What is your approximate annual family income in INR?",
        "gender": "What is your gender?",
        "caste_category": "What is your social category (General/SC/ST/OBC/EWS)?",
        "is_bpl": "Do you hold a Below Poverty Line (BPL) card?",
        "is_disabled": "Do you have a disability certificate?",
        "has_land": "Do you own agricultural land?",
    }

    missing: set[str] = set()
    for result in eligibility_results:
        missing.update(result.missing_information)

    profile_ctx = profile.to_rule_context()
    missing = {f for f in missing if f not in profile_ctx or profile_ctx[f] is None}

    questions = []
    for field in sorted(missing):
        if field in field_questions:
            questions.append(field_questions[field])
        if len(questions) >= max_questions:
            break

    return questions
