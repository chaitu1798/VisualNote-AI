# VisualNote AI

> **Turn videos into visual knowledge.**  
> *Don't summarize everything. Visualize what matters.*

VisualNote AI is an AI-powered visual learning platform that converts educational videos and lecture sources into structured, visually organized handwritten-style study pages, diagrams, and revision sheets.

---

## Key Features (P0 Foundation)
- **Deterministic Presentation Separation**: Educational text, formulas (KaTeX), and diagrams (SVG) are rendered deterministically; image generation provides purely decorative styling without text hallucination.
- **Microservice/Modular Monorepo**: Next.js 14 App Router frontend and FastAPI asynchronous backend.
- **Relational Integrity**: PostgreSQL 15 with SQLAlchemy 2.0 and Alembic schema migrations.
- **Job Orchestration**: Background worker infrastructure with Redis 7.
- **Granular Health Diagnostics**: Dedicated multi-tier dependency monitoring at `/api/v1/health`.

---

## Monorepo Layout

```text
visualnote/
├── apps/
│   ├── web/               # Next.js 14 App Router, TypeScript, Tailwind CSS
│   └── api/               # FastAPI Backend, SQLAlchemy 2.0, Alembic
├── packages/
│   └── types/             # Shared TypeScript definitions
├── docs/
│   ├── architecture.md    # System design & core thesis
│   └── setup.md           # Step-by-step developer installation
├── docker-compose.yml     # PostgreSQL 15 & Redis 7
├── .env.example           # Documented environment variables
└── README.md
```

---

## Development Quickstart

### 1. Launch Infrastructure
```bash
docker compose up -d
```

### 2. Launch Backend
```bash
cd apps/api
uv venv .venv --python 3.11
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
alembic upgrade head
pytest -v
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Launch Frontend
```bash
cd apps/web
npm.cmd install
npm.cmd run dev
```

Visit:
- **Web App**: `http://localhost:3000`
- **Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/v1/health`
