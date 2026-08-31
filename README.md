# GovtAssist AI

**AI-Powered Government Scheme Discovery & Eligibility Assistant**

GovtAssist AI helps Indian citizens discover central and state government schemes they may be eligible for. It combines **AI profile extraction**, a **deterministic rules engine**, and **RAG-based document retrieval** to deliver personalized, source-grounded recommendations.

> Results indicate **potential eligibility only**. Always verify on official government portals before applying.

---

## Architecture

```
User Query → Profile Agent → Scheme Search → Rules Engine → RAG Retrieval → Recommendations
```

| Component | Role |
|-----------|------|
| **Profile Agent** | Extracts structured profile from natural language (LLM + fallback parser) |
| **Scheme Search** | Filters schemes by state, keywords, and metadata |
| **Rules Engine** | Deterministic eligibility evaluation — LLMs do NOT decide eligibility |
| **RAG Agent** | Retrieves official scheme document context via pgvector |
| **Recommendation Engine** | Ranks and scores schemes, generates follow-up questions |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 |
| AI | OpenAI API, LangGraph-ready orchestrator |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7 |
| Frontend | Next.js 15, React 19, Tailwind CSS |
| DevOps | Docker Compose, GitHub Actions CI |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- **OR** Python 3.12+, Node.js 20+, PostgreSQL with pgvector

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/govtassist-ai.git
cd govtassist-ai
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Local Development

```bash
# 1. Start PostgreSQL + Redis
docker compose up postgres redis -d

# 2. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python -m scripts.seed_data
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key for LLM features |
| `LLM_MOCK_MODE=true` | Run without API key (rule-based fallback) |
| `DATABASE_URL` | PostgreSQL connection string |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/schemes` | List schemes (filterable) |
| `GET` | `/api/v1/schemes/{id}` | Scheme details |
| `POST` | `/api/v1/recommendations` | Get personalized recommendations |
| `POST` | `/api/v1/recommendations/extract-profile` | Extract profile from text |

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I am 23 years old, a graduate from Haryana, family income is 4 lakh"
  }'
```

## Project Structure

```
govtassist-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents (profile, search, eligibility, orchestrator)
│   │   ├── api/routes/      # FastAPI route handlers
│   │   ├── engine/          # Rules engine + recommendation ranking
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── rag/             # Vector retrieval (pgvector)
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # LLM service
│   ├── scripts/seed_data.py # Database seeder (10 real schemes)
│   └── tests/               # Unit tests
├── frontend/
│   └── src/app/             # Next.js App Router pages
├── docker-compose.yml
├── .github/workflows/ci.yml
└── Makefile
```

## Seeded Schemes

The database ships with 10 real government schemes including:

- PM-KISAN, PM-JAY, Stand-Up India, PMKVY
- National Scholarship Portal, MUDRA, PMAY, Sukanya Samriddhi
- Haryana Merit Scholarship, Haryana Unemployment Allowance

## Testing

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

## Design Principles

1. **LLMs do not determine eligibility** — structured rules handle decisions
2. **All responses grounded in official documents** via RAG
3. **Every recommendation includes source URLs**
4. **Eligibility classified as**: Likely Eligible, Possibly Eligible, Insufficient Info
5. **Missing information collected via follow-up questions**

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Disclaimer

This platform provides informational assistance only. It is not affiliated with any government body. Final eligibility and benefits must be confirmed through official government channels.
