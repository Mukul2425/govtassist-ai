"""Agent orchestrator with multi-turn session support."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.eligibility_agent import evaluate_schemes
from app.agents.profile_agent import extract_profile
from app.agents.search_agent import search_schemes
from app.engine.recommendation_engine import generate_follow_up_questions, rank_schemes
from app.logging_config import get_logger
from app.models.scheme import QuerySession
from app.rag.retriever import retrieve_scheme_context
from app.schemas.profile import UserProfile
from app.schemas.recommendation import RecommendationResponse, SchemeRecommendation
from app.services.llm_service import llm_service

logger = get_logger(__name__)

DISCLAIMER = (
    "These recommendations indicate potential eligibility based on the information provided. "
    "Final eligibility must be confirmed through official government authorities, "
    "portals, or designated offices. Scheme details, rules, and deadlines may change. "
    "Always verify on the official source before applying."
)


class RecommendationOrchestrator:
    async def _load_session_profile(
        self,
        session: AsyncSession,
        session_id: str | None,
    ) -> UserProfile | None:
        if not session_id:
            return None
        result = await session.execute(
            select(QuerySession).where(QuerySession.id == session_id)
        )
        row = result.scalar_one_or_none()
        if row and row.extracted_profile:
            return UserProfile.model_validate(row.extracted_profile)
        return None

    async def run(
        self,
        session: AsyncSession,
        query: str,
        profile: UserProfile | None = None,
        session_id: str | None = None,
        max_results: int = 10,
    ) -> RecommendationResponse:
        new_session_id = session_id or str(uuid4())

        prior_profile = await self._load_session_profile(session, session_id)
        base_profile = profile or prior_profile

        extraction = await extract_profile(query, base_profile)
        user_profile = extraction.profile

        schemes = await search_schemes(session, user_profile, query)
        eligibility_results = evaluate_schemes(user_profile, schemes)
        ranked = rank_schemes(eligibility_results, user_profile, max_results)

        scheme_map = {s.id: s for s in schemes}
        recommendations: list[SchemeRecommendation] = []

        for result in ranked:
            scheme = scheme_map.get(result.scheme_id)
            if not scheme:
                continue

            context = await retrieve_scheme_context(session, scheme.id, query, top_k=2)
            why = await llm_service.generate_why_eligible(
                scheme.name,
                user_profile,
                [r.model_dump() for r in result.rule_details if r.passed],
            )

            recommendations.append(
                SchemeRecommendation(
                    scheme_id=scheme.id,
                    scheme_name=scheme.name,
                    short_description=scheme.short_description,
                    eligibility_status=result.eligibility_status,
                    eligibility_score=result.score,
                    why_eligible=why,
                    benefits=scheme.benefits,
                    required_documents=scheme.required_documents,
                    application_process=scheme.application_process,
                    application_url=scheme.application_url,
                    official_source_url=scheme.official_source_url,
                    missing_information=result.missing_information,
                    retrieved_context=context,
                )
            )

        follow_ups = generate_follow_up_questions(eligibility_results, user_profile)
        summary = await llm_service.generate_explanation(
            query, user_profile, [r.model_dump() for r in recommendations]
        )

        if session_id:
            result = await session.execute(
                select(QuerySession).where(QuerySession.id == session_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.user_query = query
                existing.extracted_profile = user_profile.model_dump(exclude_none=True)
                existing.recommendations = [r.model_dump() for r in recommendations]
                existing.response_text = summary
            else:
                session.add(
                    QuerySession(
                        id=new_session_id,
                        user_query=query,
                        extracted_profile=user_profile.model_dump(exclude_none=True),
                        recommendations=[r.model_dump() for r in recommendations],
                        response_text=summary,
                    )
                )
        else:
            session.add(
                QuerySession(
                    id=new_session_id,
                    user_query=query,
                    extracted_profile=user_profile.model_dump(exclude_none=True),
                    recommendations=[r.model_dump() for r in recommendations],
                    response_text=summary,
                )
            )

        logger.info(
            "recommendation_complete",
            session_id=new_session_id,
            recommendations=len(recommendations),
            continued=bool(session_id),
        )

        return RecommendationResponse(
            session_id=new_session_id,
            query=query,
            extracted_profile=user_profile,
            recommendations=recommendations,
            follow_up_questions=follow_ups,
            disclaimer=DISCLAIMER,
            response_summary=summary,
        )


orchestrator = RecommendationOrchestrator()
