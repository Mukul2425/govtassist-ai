"""Deterministic eligibility rules engine.

Evaluates user profiles against structured scheme rules without LLM involvement.
Supports operators: eq, ne, gt, gte, lt, lte, in, not_in, contains, exists
"""

from typing import Any

from app.logging_config import get_logger
from app.schemas.profile import UserProfile
from app.schemas.recommendation import (
    EligibilityResult,
    EligibilityStatus,
    RuleEvaluationResult,
)

logger = get_logger(__name__)

OPERATORS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "in": lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
    "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple, set)) else True,
    "contains": lambda a, b: b in a if isinstance(a, (list, tuple, str)) else False,
    "exists": lambda a, _b: a is not None,
}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.lower().strip().replace(" ", "_")
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    return value


def evaluate_rule(
    profile_ctx: dict[str, Any],
    field: str,
    operator: str,
    expected: Any,
    is_required: bool = True,
    description: str | None = None,
) -> RuleEvaluationResult:
    actual = profile_ctx.get(field)
    op_fn = OPERATORS.get(operator)

    if op_fn is None:
        logger.warning("unknown_operator", operator=operator, field=field)
        return RuleEvaluationResult(
            field=field,
            operator=operator,
            expected=expected,
            actual=actual,
            passed=False,
            is_required=is_required,
            description=description,
        )

    if actual is None:
        passed = not is_required
        return RuleEvaluationResult(
            field=field,
            operator=operator,
            expected=expected,
            actual=actual,
            passed=passed,
            is_required=is_required,
            description=description,
        )

    norm_actual = _normalize_value(actual)
    norm_expected = _normalize_value(expected)

    try:
        passed = op_fn(norm_actual, norm_expected)
    except (TypeError, ValueError):
        passed = False

    return RuleEvaluationResult(
        field=field,
        operator=operator,
        expected=expected,
        actual=actual,
        passed=passed,
        is_required=is_required,
        description=description,
    )


def evaluate_eligibility(
    profile: UserProfile,
    scheme_id: str,
    scheme_name: str,
    rules: list[dict[str, Any]],
) -> EligibilityResult:
    ctx = profile.to_rule_context()
    results: list[RuleEvaluationResult] = []

    for rule in rules:
        results.append(
            evaluate_rule(
                profile_ctx=ctx,
                field=rule["field"],
                operator=rule["operator"],
                expected=rule["value"],
                is_required=rule.get("is_required", True),
                description=rule.get("description"),
            )
        )

    required_results = [r for r in results if r.is_required]
    matched = sum(1 for r in required_results if r.passed)
    failed = sum(1 for r in required_results if not r.passed and r.actual is not None)
    missing = list({r.field for r in required_results if r.actual is None and r.is_required})

    total_required = len(required_results)

    if missing:
        if matched > 0 and failed == 0:
            status = EligibilityStatus.POSSIBLY_ELIGIBLE
        elif matched == 0 and failed == 0:
            status = EligibilityStatus.INSUFFICIENT_INFO
        else:
            status = EligibilityStatus.INSUFFICIENT_INFO
    elif failed == 0:
        status = EligibilityStatus.LIKELY_ELIGIBLE
    elif matched >= total_required * 0.6:
        status = EligibilityStatus.POSSIBLY_ELIGIBLE
    else:
        status = EligibilityStatus.NOT_ELIGIBLE

    if total_required == 0:
        score = 50.0
    else:
        score = (matched / total_required) * 100
        if status == EligibilityStatus.LIKELY_ELIGIBLE:
            score = min(100.0, score + 10)
        elif status == EligibilityStatus.NOT_ELIGIBLE:
            score = max(0.0, score - 20)

    return EligibilityResult(
        scheme_id=scheme_id,
        scheme_name=scheme_name,
        eligibility_status=status,
        matched_rules=matched,
        failed_rules=failed,
        total_rules=total_required,
        missing_information=missing,
        rule_details=results,
        score=round(score, 2),
    )
