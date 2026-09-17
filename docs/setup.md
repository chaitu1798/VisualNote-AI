# VisualNote AI — Developer Setup Guide

## Prerequisites
- **Node.js**: v20+ (v24 supported)
- **Python**: 3.11 or 3.12 (managed via `uv` or system Python)
- **Docker & Docker Compose**: For PostgreSQL and Redis containers

---

## 1. Quickstart (Windows PowerShell)

### Step 1: Start Infrastructure (PostgreSQL & Redis)
```powershell
# From the repository root:
docker compose up -d

# Verify services are running and healthy:
docker compose ps
```

### Step 2: Backend Setup
```powershell
cd apps/api

# Create virtual environment with Python 3.11 using uv:
uv venv .venv --python 3.11

# Activate virtual environment:
.\.venv\Scripts\Activate.ps1

# Install backend dependencies:
uv pip install -r requirements.txt

# Run database migrations:
alembic upgrade head

# Run backend automated test suite:
pytest -v

# Start FastAPI development server:
python -m uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at: `http://localhost:8000/docs`  
Health Check endpoint: `http://localhost:8000/api/v1/health`

### Step 3: Frontend Setup
```powershell
# In a new terminal from repository root:
cd apps/web

# Install frontend dependencies:
npm.cmd install

# Start Next.js development server:
npm.cmd run dev
```
Open `http://localhost:3000` to view the web application.

---

## 2. Environment Configuration
Copy `.env.example` to `.env` in the root and in `apps/api/` as needed:
```powershell
Copy-Item .env.example .env
```
Ensure `DATABASE_URL` and `REDIS_URL` point to the running Docker services.
