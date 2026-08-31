"""Seed database with government schemes and eligibility rules."""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.database import Base
from app.models.scheme import EligibilityRule, GovernmentLevel, Scheme, SchemeDocument

settings = get_settings()

SCHEMES_DATA = [
    {
        "id": "SCH_PM_KISAN",
        "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "short_description": "Income support of ₹6,000/year in 3 installments to eligible farmer families.",
        "full_description": (
            "PM-KISAN is a Central Sector scheme providing income support of ₹6,000 per year "
            "to all landholding farmer families across the country, payable in three equal "
            "installments of ₹2,000 each directly into bank accounts."
        ),
        "government_level": GovernmentLevel.CENTRAL,
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "category": "Agriculture",
        "applicable_states": ["All India"],
        "benefits": [
            "₹6,000 per year in 3 installments of ₹2,000",
            "Direct Benefit Transfer to bank account",
            "Covers all landholding farmer families",
        ],
        "required_documents": [
            "Aadhaar Card",
            "Land ownership records",
            "Bank account details",
        ],
        "application_process": (
            "Register through PM-KISAN portal or visit nearest Common Service Centre (CSC). "
            "State/UT governments verify land records and approve beneficiaries."
        ),
        "application_url": "https://pmkisan.gov.in/",
        "official_source_url": "https://pmkisan.gov.in/",
        "keywords": ["farmer", "agriculture", "income support", "kisan"],
        "rules": [
            {"field": "occupation", "operator": "eq", "value": "farmer", "description": "Must be a farmer"},
            {"field": "has_land", "operator": "eq", "value": True, "description": "Must own agricultural land", "is_required": False},
        ],
        "documents": [
            {
                "title": "PM-KISAN Overview",
                "content": "PM-KISAN provides ₹6,000/year to landholding farmer families. Excludes institutional landholders, government employees, income tax payers in last assessment year.",
                "source_url": "https://pmkisan.gov.in/",
            }
        ],
    },
    {
        "id": "SCH_PM_JAY",
        "name": "Ayushman Bharat - PM-JAY",
        "short_description": "Health insurance cover of ₹5 lakh per family per year for secondary and tertiary care.",
        "full_description": (
            "Ayushman Bharat PM-JAY is the world's largest health insurance scheme providing "
            "coverage of ₹5 lakh per family per year for secondary and tertiary hospitalization "
            "to over 12 crore poor and vulnerable families."
        ),
        "government_level": GovernmentLevel.CENTRAL,
        "ministry": "Ministry of Health & Family Welfare",
        "category": "Health",
        "applicable_states": ["All India"],
        "benefits": [
            "₹5 lakh health cover per family per year",
            "Covers 1,929 treatment procedures",
            "Cashless treatment at empanelled hospitals",
        ],
        "required_documents": ["Aadhaar Card", "Ration Card or SECC data verification"],
        "application_process": "Eligible families are auto-identified via SECC 2011 data. Visit nearest Ayushman Mitra at empanelled hospital for card generation.",
        "application_url": "https://pmjay.gov.in/",
        "official_source_url": "https://pmjay.gov.in/",
        "keywords": ["health", "insurance", "hospital", "medical"],
        "rules": [
            {"field": "is_bpl", "operator": "eq", "value": True, "description": "BPL/SECC identified family", "is_required": False},
            {"field": "annual_family_income", "operator": "lte", "value": 500000, "description": "Income below ₹5 lakh", "is_required": False},
        ],
        "documents": [
            {
                "title": "PM-JAY Eligibility",
                "content": "Covers families identified through SECC 2011 database. No enrollment fee. Pre-existing conditions covered from day one.",
                "source_url": "https://pmjay.gov.in/",
            }
        ],
    },
    {
        "id": "SCH_STANDUP_INDIA",
        "name": "Stand-Up India Scheme",
        "short_description": "Bank loans between ₹10 lakh and ₹1 crore for SC/ST and women entrepreneurs.",
        "full_description": (
            "Stand-Up India Scheme facilitates bank loans between ₹10 lakh and ₹1 crore to "
            "at least one SC/ST borrower and one woman borrower per bank branch for setting "
            "up greenfield enterprises in manufacturing, services, or trading."
        ),
        "government_level": GovernmentLevel.CENTRAL,
        "ministry": "Ministry of Finance",
        "category": "Entrepreneurship",
        "applicable_states": ["All India"],
        "benefits": [
            "Loans from ₹10 lakh to ₹1 crore",
            "Composite loan (term loan + working capital)",
            "Handholding support through SIDBI",
        ],
        "required_documents": [
            "Aadhaar/PAN",
            "Business plan",
            "Caste certificate (for SC/ST)",
            "Project report",
        ],
        "application_process": "Apply through Stand-Up India portal or visit lead bank branch. Online application at standupmitra.in.",
        "application_url": "https://www.standupmitra.in/",
        "official_source_url": "https://www.standupmitra.in/",
        "keywords": ["entrepreneur", "loan", "startup", "women", "sc", "st"],
        "rules": [
            {"field": "age", "operator": "gte", "value": 18, "description": "Minimum age 18 years"},
            {"field": "is_woman", "operator": "eq", "value": True, "description": "Women entrepreneur", "is_required": False},
            {"field": "caste_category", "operator": "in", "value": ["sc", "st"], "description": "SC/ST category", "is_required": False},
        ],
        "documents": [
            {
                "title": "Stand-Up India Details",
                "content": "At least one SC/ST and one woman borrower per bank branch. Greenfield enterprise only. Margin money as per bank norms.",
                "source_url": "https://www.standupmitra.in/",
            }
        ],
    },
    {
        "id": "SCH_PMKVY",
        "name": "PM Kaushal Vikas Yojana (PMKVY)",
        "short_description": "Free skill training and certification for Indian youth to enhance employability.",
        "full_description": (
            "PMKVY is the flagship scheme of the Ministry of Skill Development & Entrepreneurship "
            "providing free short-term training aligned to National Skills Qualification Framework "
            "with monetary rewards upon certification."
        ),
        "government_level": GovernmentLevel.CENTRAL,
        "ministry": "Ministry of Skill Development & Entrepreneurship",
        "category": "Skill Development",
        "applicable_states": ["All India"],
        "benefits": [
            "Free skill training",
            "Industry-recognized certification",
            "Monetary reward upon certification",
            "Placement assistance",
        ],
        "required_documents": ["Aadhaar Card", "Bank account details", "Educational certificates"],
        "application_process": "Register on Skill India portal or visit nearest PMKVY training centre.",
        "application_url": "https://www.pmkvyofficial.org/",
        "official_source_url": "https://www.pmkvyofficial.org/",
        "keywords": ["skill", "training", "employment", "youth", "certification"],
        "rules": [
            {"field": "age", "operator": "gte", "value": 18, "description": "Minimum age 18"},
            {"field": "age", "operator": "lte", "value": 45, "description": "Maximum age 45"},
        ],
        "documents": [
            {
                "title": "PMKVY Training",
                "content": "Short-term training (150-300 hours). Training partners empanelled by NSDC. Assessment by SSCs.",
                "source_url": "https://www.pmkvyofficial.org/",
            }
        ],
    },
    {
        "id": "SCH_NSP",
        "name": "National Scholarship Portal (NSP)",
        "short_description": "Central platform for various government scholarships for students.",
        "full_description": (
            "NSP is a one-stop solution for various scholarship schemes offered by Central and "
            "State governments. Includes Post Matric, Pre Matric, Merit-cum-Means, and Top Class "
            "Education scholarships for SC/ST/OBC/Minority/General categories."
        ),
        "government_level": GovernmentLevel.BOTH,
        "ministry": "Ministry of Education",
        "category": "Education",
        "applicable_states": ["All India"],
        "benefits": [
            "Tuition fee reimbursement",
            "Maintenance allowance",
            "Multiple scholarship schemes on one portal",
        ],
        "required_documents": [
            "Aadhaar Card",
            "Income certificate",
            "Caste/category certificate",
            "Previous year mark sheet",
            "Bank account details",
        ],
        "application_process": "Register and apply on scholarships.gov.in during application window.",
        "application_url": "https://scholarships.gov.in/",
        "official_source_url": "https://scholarships.gov.in/",
        "keywords": ["scholarship", "student", "education", "college"],
        "rules": [
            {"field": "occupation", "operator": "eq", "value": "student", "description": "Must be a student", "is_required": False},
            {"field": "education", "operator": "in", "value": ["class_10", "class_12", "graduate", "post_graduate"], "description": "Enrolled in recognized institution"},
        ],
        "documents": [
            {
                "title": "NSP Scholarships",
                "content": "Multiple schemes: Post Matric Scholarship for SC/ST/OBC, Merit-cum-Means for minority communities, Central Sector Scheme for Top Class Education.",
                "source_url": "https://scholarships.gov.in/",
            }
        ],
    },
    {
        "id": "SCH_MUDRA",
        "name": "Pradhan Mantri MUDRA Yojana",
        "short_description": "Collateral-free loans up to ₹10 lakh for non-farm micro enterprises.",
        "full_description": (
            "PMMY provides loans up to ₹10 lakh to non-corporate, non-farm small/micro enterprises. "
            "Three categories: Shishu (up to ₹50,000), Kishore (₹50,001-₹5 lakh), Tarun (₹5-10 lakh)."
        ),
        "government_level": GovernmentLevel.CENTRAL,
        "ministry": "Ministry of Finance",
        "category": "Micro Finance",
        "applicable_states": ["All India"],
        "benefits": [
            "Collateral-free loans up to ₹10 lakh",
            "Shishu/Kishore/Tarun categories",
            "Available through banks, NBFCs, MFIs",
        ],
        "required_documents": ["Aadhaar/PAN", "Business proof", "Bank statements", "Project report"],
        "application_process": "Apply at any bank, NBFC, or MFI branch. Also available through Udyamimitra portal.",
        "application_url": "https://www.mudra.org.in/",
        "official_source_url": "https://www.mudra.org.in/",
        "keywords": ["loan", "business", "micro enterprise", "self employed"],
        "rules": [
            {"field": "occupation", "operator": "in", "value": ["self_employed", "business"], "description": "Non-farm micro enterprise"},
            {"field": "age", "operator": "gte", "value": 18, "description": "Minimum age 18"},
        ],
        "documents": [
            {
                "title": "MUDRA Loan Categories",
                "content": "Shishu: up to ₹50K for startups. Kishore: ₹50K-5L for established businesses. Tarun: ₹5L-10L for expansion.",
                "source_url": "https://www.mudra.org.in/",
            }
        ],
    },
    {
        "id": "SCH_HRY_MERIT",
        "name": "Haryana Merit Scholarship Scheme",
        "short_description": "State scholarship for meritorious students from Haryana in higher education.",
        "full_description": (
            "Haryana government provides merit-based scholarships to domicile students pursuing "
            "higher education in recognized institutions within or outside the state."
        ),
        "government_level": GovernmentLevel.STATE,
        "ministry": "Department of Higher Education, Haryana",
        "category": "Education",
        "applicable_states": ["Haryana"],
        "benefits": [
            "Monthly scholarship stipend",
            "Covers tuition for eligible courses",
            "Renewable based on academic performance",
        ],
        "required_documents": [
            "Domicile certificate of Haryana",
            "Aadhaar Card",
            "Previous academic mark sheets",
            "Admission proof",
            "Income certificate",
        ],
        "application_process": "Apply through Haryana Scholarship Portal (hryedumis.gov.in) during notification period.",
        "application_url": "https://hryedumis.gov.in/",
        "official_source_url": "https://hryedumis.gov.in/",
        "keywords": ["haryana", "scholarship", "merit", "student", "graduate"],
        "rules": [
            {"field": "state", "operator": "eq", "value": "haryana", "description": "Must be Haryana domicile"},
            {"field": "education", "operator": "in", "value": ["graduate", "post_graduate"], "description": "Pursuing higher education"},
            {"field": "annual_family_income", "operator": "lte", "value": 400000, "description": "Family income up to ₹4 lakh"},
        ],
        "documents": [
            {
                "title": "Haryana Merit Scholarship",
                "content": "For students with minimum 60% marks in previous examination. Domicile of Haryana mandatory. Income ceiling applies.",
                "source_url": "https://hryedumis.gov.in/",
            }
        ],
    },
    {
        "id": "SCH_HRY_UNEMPLOYMENT",
        "name": "Haryana Unemployment Allowance Scheme",
        "short_description": "Monthly allowance for educated unemployed youth in Haryana.",
        "full_description": (
            "Haryana provides unemployment allowance to educated unemployed youth who are domiciled "
            "in the state and actively seeking employment."
        ),
        "government_level": GovernmentLevel.STATE,
        "ministry": "Department of Employment, Haryana",
        "category": "Employment",
        "applicable_states": ["Haryana"],
        "benefits": [
            "Monthly unemployment allowance",
            "Job placement assistance",
            "Skill training referrals",
        ],
        "required_documents": [
            "Domicile certificate",
            "Educational certificates",
            "Aadhaar Card",
            "Unemployment registration proof",
        ],
        "application_process": "Register on Haryana Employment Department portal and apply for allowance.",
        "application_url": "https://hrex.gov.in/",
        "official_source_url": "https://hrex.gov.in/",
        "keywords": ["haryana", "unemployment", "allowance", "graduate", "youth"],
        "rules": [
            {"field": "state", "operator": "eq", "value": "haryana", "description": "Haryana domicile required"},
            {"field": "occupation", "operator": "eq", "value": "unemployed", "description": "Must be unemployed"},
            {"field": "education", "operator": "in", "value": ["graduate", "post_graduate"], "description": "Graduate or above"},
            {"field": "age", "operator": "gte", "value": 21, "description": "Minimum age 21"},
            {"field": "age", "operator": "lte", "value": 35, "description": "Maximum age 35"},
        ],
        "documents": [
            {
                "title": "Haryana Unemployment Allowance",
                "content": "For graduates aged 21-35 who are Haryana domicile. Must register with employment exchange. Allowance for up to 3 years.",
                "source_url": "https://hrex.gov.in/",
            }
        ],
    },
    {
        "id": "SCH_PMAY",
        "name": "Pradhan Mantri Awas Yojana (PMAY)",
        "short_description": "Affordable housing scheme with credit-linked subsidy for urban and rural beneficiaries.",
        "full_description": (
            "PMAY aims to provide affordable housing to the urban and rural poor by 2024. "
            "Includes Credit Linked Subsidy Scheme (CLSS) for home loans and direct housing construction assistance."
        ),
        "government_level": GovernmentLevel.CENTRAL,
        "ministry": "Ministry of Housing & Urban Affairs",
        "category": "Housing",
        "applicable_states": ["All India"],
        "benefits": [
            "Interest subsidy on home loans up to ₹2.67 lakh",
            "Direct assistance for house construction",
            "Affordable housing in partnership (AHP)",
        ],
        "required_documents": [
            "Aadhaar Card",
            "Income certificate",
            "Property documents (if applicable)",
            "Bank account details",
        ],
        "application_process": "Apply through PMAY portal or Common Service Centre. Verify eligibility via income and property criteria.",
        "application_url": "https://pmaymis.gov.in/",
        "official_source_url": "https://pmaymis.gov.in/",
        "keywords": ["housing", "home", "loan", "subsidy", "urban", "rural"],
        "rules": [
            {"field": "annual_family_income", "operator": "lte", "value": 1800000, "description": "EWS/LIG/MIG income criteria"},
        ],
        "documents": [
            {
                "title": "PMAY Income Categories",
                "content": "EWS: up to ₹3L/year, LIG: ₹3-6L, MIG-I: ₹6-12L, MIG-II: ₹12-18L. No pucca house ownership in name of any family member.",
                "source_url": "https://pmaymis.gov.in/",
            }
        ],
    },
    {
        "id": "SCH_SUkanya",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "short_description": "Small savings scheme for girl child with attractive interest rate and tax benefits.",
        "full_description": (
            "SSY is a government-backed savings scheme for girl children under 10 years. "
            "Offers high interest rate (currently 8.2% p.a.) with tax benefits under Section 80C."
        ),
        "government_level": GovernmentLevel.CENTRAL,
        "ministry": "Ministry of Finance",
        "category": "Savings",
        "applicable_states": ["All India"],
        "benefits": [
            "Attractive interest rate (~8.2% p.a.)",
            "Tax deduction under Section 80C",
            "Maturity at 21 years or on marriage after 18",
        ],
        "required_documents": [
            "Girl child's birth certificate",
            "Parent/guardian identity proof",
            "Address proof",
        ],
        "application_process": "Open account at post office or authorized bank with required documents.",
        "application_url": "https://www.indiapost.gov.in/",
        "official_source_url": "https://www.nsiindia.gov.in/",
        "keywords": ["girl child", "savings", "ssy", "daughter"],
        "rules": [
            {"field": "gender", "operator": "eq", "value": "female", "description": "For girl child", "is_required": False},
        ],
        "documents": [
            {
                "title": "SSY Account Rules",
                "content": "Account can be opened for girl child below 10 years. Minimum deposit ₹250/year, maximum ₹1.5 lakh/year. Partial withdrawal allowed for education after 18.",
                "source_url": "https://www.nsiindia.gov.in/",
            }
        ],
    },
]


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        from sqlalchemy import select

        existing = await session.execute(select(Scheme).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        now = datetime.now(UTC)
        for data in SCHEMES_DATA:
            rules = data.pop("rules")
            docs = data.pop("documents")

            scheme = Scheme(**data, verified_at=now, is_active=True)
            session.add(scheme)
            await session.flush()

            for rule in rules:
                session.add(EligibilityRule(scheme_id=scheme.id, **rule))

            for i, doc in enumerate(docs):
                session.add(
                    SchemeDocument(
                        scheme_id=scheme.id,
                        title=doc["title"],
                        content=doc["content"],
                        chunk_index=i,
                        source_url=doc["source_url"],
                    )
                )

        await session.commit()
        print(f"Seeded {len(SCHEMES_DATA)} schemes successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
