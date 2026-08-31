"""Eligibility evaluation agent — wraps deterministic rules engine."""

from app.engine.rules_engine import evaluate_eligibility
from app.logging_config import get_logger
from app.models.scheme import Scheme
from app.schemas.profile import UserProfile
from app.schemas.recommendation import EligibilityResult

logger = get_logger(__name__)


def evaluate_schemes(
    profile: UserProfile,
    schemes: list[Scheme],
) -> list[EligibilityResult]:
    results: list[EligibilityResult] = []

    for scheme in schemes:
        rules = [
            {
                "field": r.field,
                "operator": r.operator,
                "value": r.value,
                "is_required": r.is_required,
                "description": r.description,
            }
            for r in scheme.eligibility_rules
        ]

        result = evaluate_eligibility(
            profile=profile,
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            rules=rules,
        )
        results.append(result)

    logger.info(
        "eligibility_evaluated",
        total=len(results),
        likely=sum(1 for r in results if r.eligibility_status.value == "likely_eligible"),
    )

    return results
