"""Tests for the deterministic eligibility rules engine."""

from app.engine.rules_engine import evaluate_eligibility, evaluate_rule
from app.schemas.profile import UserProfile
from app.schemas.recommendation import EligibilityStatus


class TestEvaluateRule:
    def test_age_gte_pass(self):
        result = evaluate_rule({"age": 25}, "age", "gte", 18)
        assert result.passed is True

    def test_age_gte_fail(self):
        result = evaluate_rule({"age": 15}, "age", "gte", 18)
        assert result.passed is False

    def test_income_lte_pass(self):
        result = evaluate_rule({"annual_family_income": 400000}, "annual_family_income", "lte", 500000)
        assert result.passed is True

    def test_state_in_pass(self):
        result = evaluate_rule({"state": "haryana"}, "state", "eq", "haryana")
        assert result.passed is True

    def test_missing_required_field(self):
        result = evaluate_rule({}, "age", "gte", 18, is_required=True)
        assert result.passed is False
        assert result.actual is None

    def test_missing_optional_field(self):
        result = evaluate_rule({}, "is_bpl", "eq", True, is_required=False)
        assert result.passed is True

    def test_in_operator(self):
        result = evaluate_rule({"education": "graduate"}, "education", "in", ["graduate", "post_graduate"])
        assert result.passed is True


class TestEvaluateEligibility:
    def test_likely_eligible(self):
        profile = UserProfile(
            age=23,
            state="Haryana",
            education="graduate",
            annual_family_income=400000,
            occupation="unemployed",
        )
        rules = [
            {"field": "state", "operator": "eq", "value": "haryana", "is_required": True},
            {"field": "education", "operator": "in", "value": ["graduate", "post_graduate"], "is_required": True},
            {"field": "annual_family_income", "operator": "lte", "value": 500000, "is_required": True},
            {"field": "occupation", "operator": "eq", "value": "unemployed", "is_required": True},
        ]
        result = evaluate_eligibility(profile, "SCH_TEST", "Test Scheme", rules)
        assert result.eligibility_status == EligibilityStatus.LIKELY_ELIGIBLE
        assert result.matched_rules == 4
        assert result.failed_rules == 0

    def test_not_eligible(self):
        profile = UserProfile(age=40, state="Maharashtra", education="class_10")
        rules = [
            {"field": "state", "operator": "eq", "value": "haryana", "is_required": True},
            {"field": "education", "operator": "in", "value": ["graduate"], "is_required": True},
        ]
        result = evaluate_eligibility(profile, "SCH_TEST", "Test Scheme", rules)
        assert result.eligibility_status == EligibilityStatus.NOT_ELIGIBLE

    def test_insufficient_info(self):
        profile = UserProfile(state="Haryana")
        rules = [
            {"field": "state", "operator": "eq", "value": "haryana", "is_required": True},
            {"field": "age", "operator": "gte", "value": 18, "is_required": True},
            {"field": "education", "operator": "in", "value": ["graduate"], "is_required": True},
        ]
        result = evaluate_eligibility(profile, "SCH_TEST", "Test Scheme", rules)
        assert result.eligibility_status == EligibilityStatus.POSSIBLY_ELIGIBLE
        assert "age" in result.missing_information

    def test_haryana_graduate_scenario(self):
        """Test the example from project spec: graduate from Haryana, ₹4 lakh income."""
        profile = UserProfile(
            age=23,
            state="Haryana",
            education="graduate",
            annual_family_income=400000,
        )
        rules = [
            {"field": "state", "operator": "eq", "value": "haryana", "is_required": True},
            {"field": "education", "operator": "in", "value": ["graduate", "post_graduate"], "is_required": True},
            {"field": "annual_family_income", "operator": "lte", "value": 400000, "is_required": True},
        ]
        result = evaluate_eligibility(profile, "SCH_HRY_MERIT", "Haryana Merit Scholarship", rules)
        assert result.eligibility_status == EligibilityStatus.LIKELY_ELIGIBLE
        assert result.score >= 90
