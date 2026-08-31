# Contributing to GovtAssist AI

Thank you for your interest in contributing! This document provides guidelines for development.

## Development Setup

1. Fork and clone the repository
2. Copy `.env.example` to `.env`
3. Start infrastructure: `docker compose up postgres redis -d`
4. Install dependencies: `make install`
5. Seed database: `make seed`
6. Run backend: `make backend`
7. Run frontend: `make frontend`

## Code Style

### Python (Backend)

- Follow PEP 8, enforced by **Ruff**
- Use type hints on all functions
- Run `ruff check app/ tests/` before committing
- Keep business logic in `engine/` and `agents/`, not in route handlers

### TypeScript (Frontend)

- Use strict TypeScript
- Follow Next.js App Router conventions
- Run `npm run lint` before committing

## Architecture Guidelines

1. **Never use LLM for eligibility decisions** — use `engine/rules_engine.py`
2. **All scheme data must include `official_source_url`**
3. **New schemes go in `scripts/seed_data.py`** (or a future admin API)
4. **Agent changes should maintain the pipeline**: Profile → Search → Eligibility → RAG → Recommend

## Adding a New Scheme

Add an entry to `SCHEMES_DATA` in `backend/scripts/seed_data.py`:

```python
{
    "id": "SCH_UNIQUE_ID",
    "name": "Scheme Name",
    "short_description": "...",
    "full_description": "...",
    "government_level": GovernmentLevel.CENTRAL,
    "ministry": "...",
    "category": "...",
    "applicable_states": ["All India"],
    "benefits": ["..."],
    "required_documents": ["..."],
    "application_process": "...",
    "application_url": "https://...",
    "official_source_url": "https://...",
    "keywords": ["..."],
    "rules": [
        {"field": "age", "operator": "gte", "value": 18, "description": "Min age 18"},
    ],
    "documents": [
        {"title": "...", "content": "...", "source_url": "https://..."},
    ],
}
```

### Supported Rule Operators

| Operator | Description |
|----------|-------------|
| `eq` | Equal |
| `ne` | Not equal |
| `gt`, `gte`, `lt`, `lte` | Numeric comparisons |
| `in`, `not_in` | List membership |
| `contains` | String/list contains |
| `exists` | Field is present |

## Testing

- Write tests for rules engine changes in `backend/tests/`
- Run `make test` before submitting PRs
- CI runs automatically on push/PR

## Pull Request Process

1. Create a feature branch from `main`
2. Make focused, atomic commits
3. Ensure CI passes
4. Fill out the PR template
5. Request review

## Reporting Issues

Use GitHub Issues with the provided templates for bugs and feature requests.
