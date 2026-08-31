"""LLM service with OpenAI integration and mock fallback."""

import json
import re
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.logging_config import get_logger
from app.schemas.profile import UserProfile

logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        if settings.openai_api_key and not settings.llm_mock_mode:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def chat(self, system: str, user: str, temperature: float = 0.2) -> str:
        if not self._client:
            return ""

        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def embed(self, text: str) -> list[float]:
        if not self._client:
            return [0.0] * 1536

        response = await self._client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def extract_profile(self, query: str) -> tuple[UserProfile, float, list[str]]:
        if not self._client:
            return self._mock_extract_profile(query)

        system = """You are a profile extraction agent for Indian government scheme eligibility.
Extract structured information from the user's natural language query.
Return ONLY valid JSON with these optional fields:
{
  "age": int,
  "state": "State name",
  "education": "below_10th|class_10|class_12|graduate|post_graduate|phd|diploma|iti",
  "occupation": "student|farmer|self_employed|salaried|unemployed|homemaker|retired|business|laborer",
  "annual_family_income": int (INR),
  "gender": "male|female|other",
  "caste_category": "SC|ST|OBC|General|EWS",
  "is_bpl": bool,
  "is_disabled": bool,
  "is_woman": bool,
  "has_land": bool,
  "district": "district name"
}
Only include fields explicitly mentioned or clearly implied. Use null for unknown fields."""

        raw = await self.chat(system, query)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                return self._mock_extract_profile(query)

        profile = UserProfile.model_validate({k: v for k, v in data.items() if v is not None})
        filled = sum(1 for v in profile.model_dump().values() if v is not None)
        confidence = min(1.0, filled / 5)
        notes = [f"Extracted {filled} profile fields via LLM"]
        return profile, confidence, notes

    def _mock_extract_profile(self, query: str) -> tuple[UserProfile, float, list[str]]:
        """Rule-based profile extraction when LLM is unavailable."""
        q = query.lower()
        profile_data: dict[str, Any] = {}
        notes = ["Using rule-based profile extraction (LLM mock mode)"]

        age_match = re.search(r"(\d{1,3})\s*(?:years?\s*old|yrs?\b|year\b)", q)
        if age_match:
            profile_data["age"] = int(age_match.group(1))

        income_patterns = [
            r"(?:income|earning|salary)[^\d]{0,30}(?:₹|rs\.?|inr\s*)?(\d+(?:\.\d+)?)\s*(lakh|lac|lpa|crore|cr)?",
            r"(?:₹|rs\.?|inr\s*)?(\d+(?:\.\d+)?)\s*(lakh|lac|lpa|crore|cr)\b",
        ]
        for pattern in income_patterns:
            income_match = re.search(pattern, q)
            if income_match:
                amount = float(income_match.group(1))
                unit = (income_match.group(2) or "").lower() if income_match.lastindex and income_match.lastindex >= 2 else ""
                if not unit and ("crore" in q[income_match.start():] or "cr" in q[income_match.start():]):
                    unit = "crore"
                elif not unit and any(u in q[income_match.start():] for u in ("lakh", "lac", "lpa")):
                    unit = "lakh"

                if unit in ("crore", "cr"):
                    profile_data["annual_family_income"] = int(amount * 10_000_000)
                elif unit in ("lakh", "lac", "lpa"):
                    profile_data["annual_family_income"] = int(amount * 100_000)
                else:
                    profile_data["annual_family_income"] = int(amount)
                break

        states = [
            "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
            "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
            "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
            "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu",
            "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal", "delhi",
        ]
        for state in states:
            if state in q:
                profile_data["state"] = state.title()
                break

        if "graduate" in q or "graduation" in q or "bachelor" in q or "b.tech" in q or "b.a" in q:
            profile_data["education"] = "graduate"
        elif "post graduate" in q or "postgraduate" in q or "master" in q or "m.tech" in q:
            profile_data["education"] = "post_graduate"
        elif "12th" in q or "class 12" in q or "intermediate" in q:
            profile_data["education"] = "class_12"
        elif "10th" in q or "class 10" in q or "matric" in q:
            profile_data["education"] = "class_10"

        if "farmer" in q or "agriculture" in q:
            profile_data["occupation"] = "farmer"
        elif "student" in q:
            profile_data["occupation"] = "student"
        elif "unemployed" in q:
            profile_data["occupation"] = "unemployed"
        elif "self employed" in q or "self-employed" in q:
            profile_data["occupation"] = "self_employed"

        if "woman" in q or "female" in q or "girl" in q:
            profile_data["gender"] = "female"
            profile_data["is_woman"] = True
        elif "man" in q or "male" in q or "boy" in q:
            profile_data["gender"] = "male"

        profile = UserProfile.model_validate(profile_data)
        filled = sum(1 for v in profile.model_dump().values() if v is not None)
        confidence = min(1.0, filled / 4) if filled else 0.3
        return profile, confidence, notes

    async def generate_explanation(
        self,
        query: str,
        profile: UserProfile,
        recommendations: list[dict[str, Any]],
    ) -> str:
        if not self._client:
            return self._mock_generate_explanation(recommendations)

        system = """You are a helpful government scheme assistant for Indian citizens.
Explain scheme recommendations clearly in simple language.
Always mention that eligibility is indicative and must be verified on official portals.
Be concise but informative. Use bullet points where helpful."""

        user_msg = json.dumps(
            {
                "user_query": query,
                "profile": profile.model_dump(exclude_none=True),
                "recommendations": recommendations,
            },
            indent=2,
        )

        return await self.chat(system, user_msg)

    def _mock_generate_explanation(self, recommendations: list[dict[str, Any]]) -> str:
        if not recommendations:
            return (
                "Based on the information provided, I couldn't find matching schemes. "
                "Please provide more details such as your age, state, education, and income."
            )

        lines = [
            f"I found {len(recommendations)} scheme(s) that may be relevant to your profile:\n"
        ]
        for i, rec in enumerate(recommendations[:5], 1):
            lines.append(
                f"{i}. **{rec['scheme_name']}** — {rec['eligibility_status'].replace('_', ' ').title()}\n"
                f"   {rec['short_description']}\n"
            )

        lines.append(
            "\n⚠️ **Disclaimer:** These results indicate potential eligibility only. "
            "Please verify on official government portals before applying."
        )
        return "\n".join(lines)

    async def generate_why_eligible(
        self,
        scheme_name: str,
        profile: UserProfile,
        rule_details: list[dict[str, Any]],
    ) -> str:
        passed = [r for r in rule_details if r.get("passed")]
        if not passed:
            return f"Additional information is needed to confirm eligibility for {scheme_name}."

        reasons = []
        for rule in passed[:4]:
            desc = rule.get("description") or f"{rule['field']} meets requirement"
            reasons.append(desc)

        if self._client:
            system = "Explain in 1-2 simple sentences why a user may be eligible for a scheme."
            user = f"Scheme: {scheme_name}\nMatched criteria: {reasons}\nProfile: {profile.model_dump(exclude_none=True)}"
            result = await self.chat(system, user, temperature=0.3)
            if result:
                return result

        return f"You may be eligible for {scheme_name} because: " + "; ".join(reasons) + "."


llm_service = LLMService()
