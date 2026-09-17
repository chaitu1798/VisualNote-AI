# Project Working Document (PWD)

## VisualNote AI — Technical & Implementation Specification (Final Year Project Edition)

**Version:** 2.0 (FYP-scoped)
**Status:** Ready for Implementation
**Architecture:** Full-stack AI web application
**Frontend:** Next.js + TypeScript
**Backend:** FastAPI + Python
**Database:** PostgreSQL
**Queue:** Redis + Celery (or FastAPI `BackgroundTasks` if Celery is too heavy for the timeline — see §23)
**Storage:** Local disk or S3-compatible storage (e.g. Supabase Storage / MinIO)
**Deployment:** Docker Compose locally; Vercel (frontend) + Render/Railway (backend) for the demo deployment

> **Scope note:** This version removes billing, multi-style generation, browser extensions, and mobile support from the build plan. Those remain in the PRD as *Future Scope* so the report can discuss vision without inflating the build. Section 33 ("Recommended First Prototype") is the actual target for the project, not the full SaaS in Sections 1–32.

---

# 1. Technical Architecture

```text
                         USER
                           │
                           ▼
                  ┌─────────────────┐
                  │    Next.js      │
                  │   Web Client    │
                  └────────┬────────┘
                           │ HTTPS
                           ▼
                  ┌─────────────────┐
                  │    FastAPI      │
                  │    Backend      │
                  └────────┬────────┘
                           │
          ┌────────────────┼─────────────────┐
          ▼                ▼                 ▼
    PostgreSQL          Redis          Object Storage
          │                │                 │
          │                ▼                 │
          │             Celery               │
          │           (workers)              │
          └────────────────┼─────────────────┘
                           ▼
                    AI Processing Pipeline
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Transcription   LLM        Image AI
        (captions/STT) (concepts)  (illustrations only)
              │            │            │
              └────────────┼────────────┘
                           ▼
                  Deterministic Layout
                     Rendering Engine
                           │
                           ▼
                    Visual Pages (PNG)
                           │
                           ▼
                     PDF Generator
```

**Key design decision carried through the whole project:** the image-generation model never renders exact text, formulas, or diagrams from scratch. It only supplies decorative/illustrative assets. All factual text, formulas, and diagram structure are rendered deterministically (HTML/CSS → image, or SVG). See §26–§28. This is the project's core technical contribution and should be the centerpiece of the report's "Design" chapter.

---

# 2. Repository Structure (trimmed)

```text
visualnote-ai/
│
├── apps/
│   ├── web/                       # Next.js frontend
│   │   ├── app/
│   │   │   ├── (auth)/login/ signup/
│   │   │   ├── dashboard/
│   │   │   ├── create/
│   │   │   └── projects/[projectId]/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   │
│   └── api/                       # FastAPI backend
│       ├── app/
│       │   ├── api/v1/
│       │   │   ├── auth/
│       │   │   ├── projects/
│       │   │   ├── generation/
│       │   │   ├── pages/
│       │   │   └── exports/
│       │   ├── core/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── services/
│       │   │   ├── transcript_service.py
│       │   │   ├── concept_service.py
│       │   │   ├── visual_planner.py
│       │   │   ├── layout_renderer.py
│       │   │   ├── image_service.py
│       │   │   └── pdf_service.py
│       │   ├── integrations/
│       │   │   ├── youtube_captions/
│       │   │   ├── llm/
│       │   │   ├── image_generation/
│       │   │   └── storage/
│       │   └── workers/
│       ├── alembic/
│       └── requirements.txt
│
├── docker-compose.yml
├── .env.example
└── README.md
```

Dropped from the original structure: `packages/ui`, `packages/config`, marketing route group, pricing/billing routes, chat module, exports beyond PDF. Add these back only if time remains after the P0 list in §32 is done.

---

# 3. Frontend Stack

* Next.js App Router, React, TypeScript
* Tailwind CSS + shadcn/ui
* TanStack Query for server state
* Zustand only if a screen genuinely needs cross-component client state (e.g. the multi-step create form) — don't introduce it globally

---

# 4. Frontend Routes (FYP scope)

```text
/
├── /login
├── /signup
│
├── /dashboard
├── /create
│
├── /projects
└── /projects/[projectId]        (notebook viewer + PDF export)
```

Removed for FYP: marketing pages, pricing, settings/billing, chat route, study-pack route. If AI chat is implemented as a stretch goal, add `/projects/[projectId]/chat` back.

---

# 5. Database Schema (FYP scope, consistent field names)

All tables below use one **canonical Concept JSON schema** — see §6 — so there is no drift between the DB, the prompts, and the API responses (this was inconsistent in the original spec and is fixed here).

## users
```text
id
email
name
password_hash        -- if not using OAuth-only
created_at
updated_at
```

## projects
```text
id
user_id
title
source_type           -- 'youtube' | 'upload'
source_url
source_duration_sec
status                 -- see §22 Project Status
learning_mode          -- 'quick' | 'standard' | 'detailed' | 'exam'  (replaces both
                        -- old `output_mode` AND the separate page_count selector —
                        -- each mode implies a target page-count range, see §12 of PRD)
visual_style            -- fixed to 'handwritten' for MVP; column kept for future styles
created_at
updated_at
```

## sources
```text
id
project_id
storage_key            -- null for youtube (no video file stored)
mime_type
duration_sec
processing_status
created_at
```

## transcripts
```text
id
project_id
language
content                -- full text
segments                -- JSON: [{start, end, text}]
source_kind             -- 'youtube_captions' | 'stt_upload'
created_at
```

## concepts
```text
id
project_id
chapter_title
title
concept_type            -- 'definition' | 'process' | 'comparison' | 'formula' |
                          -- 'architecture' | 'timeline' | 'relationship' | 'example'
importance_score         -- float 0.0–1.0 (single source of truth for importance;
                          -- 'high'/'medium'/'low' labels are derived in the UI,
                          -- not stored separately)
source_start_sec
source_end_sec
content_json             -- the canonical Concept JSON body, see §6
created_at
```

## visual_plans
```text
id
concept_id
visual_type             -- 'concept_card' | 'flowchart' | 'comparison_table' |
                          -- 'diagram' | 'formula_block' | 'concept_map' | 'timeline'
layout
generation_status
created_at
```

## pages
```text
id
project_id
page_number
title
visual_type
image_url
content_json             -- rendered content snapshot (for regeneration/debugging)
source_start_sec
source_end_sec
generation_status         -- see §23 Page Status
created_at
updated_at
```

## generation_jobs
```text
id
project_id
job_type
status                    -- see §22 Job State Machine
progress
error_message
created_at
completed_at
```

## exports
```text
id
project_id
format                   -- 'pdf'
storage_key
status
created_at
```

Dropped for FYP: `subscriptions`, `usage_records`, `chat_messages`. Add back only as stretch goals.

---

# 6. Canonical Concept JSON (single schema used everywhere)

This is the one schema referenced by the DB `content_json` column, the LLM prompts (§9), and every API response. It merges the three inconsistent shapes from the original PWD/PRD.

```json
{
  "title": "TCP Three-Way Handshake",
  "concept_type": "process",
  "importance_score": 0.94,
  "source": {
    "start": 542,
    "end": 710
  },
  "explanation": "Short factual explanation extracted from the transcript.",
  "visual_type": "flowchart",
  "steps": [
    { "name": "SYN", "description": "Client requests connection" },
    { "name": "SYN-ACK", "description": "Server acknowledges and responds" },
    { "name": "ACK", "description": "Client confirms" }
  ],
  "comparison": null,
  "formula": null
}
```

`steps`, `comparison`, and `formula` are populated depending on `concept_type`; only one is non-null per concept. This keeps one schema instead of a different shape per visual type.

---

# 7. Entity Relationships

```text
User
 └── Projects
       ├── Source (video/audio reference)
       ├── Transcript
       ├── Concepts
       │      └── Visual Plan (1:1)
       ├── Pages
       ├── Generation Jobs
       └── Exports
```

---

# 8. Processing Pipeline

## Stage 1 — Input Validation
* URL validity (YouTube) or file type/size/duration (upload)
* Duration cap for MVP demo (e.g. reject > 60 min to control cost/time)

## Stage 2 — Source Processing

**This is the section that needed the most correction in the original spec — the two input paths must use genuinely different, ToS-compliant mechanisms:**

```text
YouTube URL                              Uploaded video/audio
     ↓                                          ↓
Validate URL                          Extract audio (ffmpeg)
     ↓                                          ↓
Fetch captions via YouTube             Run local/hosted STT
Data API (timedtext) —                (e.g. Whisper)
captions only, no video/                        ↓
audio download                          Timestamped transcript
     ↓
If no captions available →
reject with a clear message
("this video has no captions;
please upload the file instead")
```

**Explicit rule for the report and the viva:** VisualNote AI never downloads YouTube video or audio streams. YouTube sources are processed only through the official captions endpoint. Any video without captions must be uploaded by the user as a file, where the app controls the audio and can legally run STT on it. This distinction should be stated as a deliberate design decision in the report, not left implicit.

## Stage 3 — Content Understanding (LLM)
Extract from transcript: title, chapters, concepts, definitions, examples, formulas, processes, comparisons — output validated against the schema in §6.

## Stage 4 — Concept Ranking
Each concept gets `importance_score` (0–1). Only concepts above a threshold (e.g. ≥ 0.6) proceed to visual generation — this is what keeps image-generation cost bounded, which matters a lot on a student budget.

## Stage 5 — Visual Planning
Maps each surviving concept to one `visual_type` + layout, using the Visual Planner prompt (§9, Prompt C).

## Stage 6 — Deterministic Layout Rendering
The layout engine (HTML/CSS or SVG templates, one per `visual_type`) renders the exact text, steps, formulas, and diagram structure from the Concept JSON. This is the step that guarantees text accuracy — it is **not** optional and should not be skipped in favor of "just prompting the image model harder."

## Stage 7 — Image Generation (decorative layer only)
A single, consistent handwritten-style prompt template generates background texture / illustrative flourishes. It never receives raw factual content to render as text.

## Stage 8 — Composition
Layout output + decorative image assets are composited into the final page PNG.

## Stage 9 — Validation (stretch goal)
If time allows, run a vision-capable model as a QA pass to catch obviously broken pages before showing them to the user. Not required for MVP — flag it as future work if cut.

## Stage 10 — PDF Assembly
Pages → cover → table of contents → pages → PDF → storage.

---

# 9. Prompt Architecture

Keep the original's separation — it's a good decision and worth keeping in the report as-is:

| Prompt | Purpose |
|---|---|
| A — Content Analyzer | Extract factual knowledge from transcript |
| B — Concept Ranker | Score concepts by importance (0–1) |
| C — Visual Planner | Assign `visual_type` + layout per concept |
| D — Image Prompt Builder | Build the decorative-only image-gen prompt (never given raw facts) |

Each prompt's output must validate against the schema in §6 before being saved (use Pydantic on the backend).

---

# 10. Diagram/Layout Templates

For FYP scope, hand-build a fixed, small set of layout templates rather than a generic diagram engine:

```text
concept_card      → title + explanation box
flowchart         → nodes + arrows (horizontal)
comparison_table  → 2-column table
formula_block     → formula (rendered via KaTeX) + explanation
timeline          → horizontal timeline with markers
concept_map       → central node + branches (simple radial layout)
```

Six templates covering the six `visual_type` values is enough to demonstrate the "concept → deterministic visual" pipeline convincingly without building a general-purpose diagramming engine.

---

# 11. Background Jobs

```text
Job types (FYP scope):
TRANSCRIBE_VIDEO
ANALYZE_CONTENT
EXTRACT_CONCEPTS
CREATE_VISUAL_PLAN
GENERATE_PAGE
GENERATE_PDF
```

Dropped: `VALIDATE_PAGE` (moved to stretch goal §8 Stage 9), `DELETE_SOURCE` (handle deletion synchronously in the API for MVP — a background job for a simple delete is overkill at this scale).

**Implementation note for the team:** if Celery + Redis adds too much setup overhead for the timeline, FastAPI's built-in `BackgroundTasks` is an acceptable substitute for a single-instance demo deployment. Note this trade-off explicitly in the report's "Implementation Decisions" section — examiners respond well to a justified simplification more than an unused Celery setup.

---

# 12. Job State Machine (fixed — original had no path to CANCELLED)

```text
PENDING → PROCESSING → COMPLETED
                ↓
              FAILED → RETRY → PROCESSING
                ↓
            CANCELLED   (user cancels from PENDING or PROCESSING)
```

Final states: `COMPLETED`, `FAILED`, `CANCELLED`.

---

# 13. Page Status

```text
PENDING → GENERATING → READY
                ↓
              FAILED → REGENERATING → READY
```

---

# 14. Project Status

```text
DRAFT → PROCESSING → ANALYZING → GENERATING → READY
                                        ↓
                                      FAILED
```

Dropped `UPLOADING` and `ARCHIVED` as separate top-level states for MVP — uploading is a sub-step of `PROCESSING`, and archiving is a stretch-goal feature.

---

# 15. API Design (FYP scope)

Base: `/api/v1`

```http
POST /auth/signup
POST /auth/login
GET  /auth/me

GET    /projects
POST   /projects
GET    /projects/{id}
DELETE /projects/{id}

POST /projects/{id}/source          # youtube URL or file upload
GET  /projects/{id}/source/status

POST /projects/{id}/generate
GET  /projects/{id}/generation      # job status/progress

GET  /projects/{id}/pages
GET  /pages/{pageId}
POST /pages/{pageId}/regenerate

POST /projects/{id}/export/pdf
GET  /projects/{id}/exports
```

Dropped: billing, chat, style-change/simplify endpoints (stretch goals only).

---

# 16. Security (keep — don't cut this for FYP)

Even a student project handling user accounts and file uploads should implement:

* authenticated API access (JWT or session)
* resource ownership checks (a user can only access their own projects)
* file type/MIME validation and upload size limits on the video upload endpoint
* signed/short-lived URLs for any private storage access
* never trust `user_id` or `project_id` sent from the frontend — always re-derive from the authenticated session

This is a natural place in the report to show security awareness without needing production-grade rate limiting or secret rotation.

---

# 17. Error Handling

Same principle as the original — user-facing errors should be specific:

> Bad: "Error 500"
> Good: "This video doesn't have captions available. Try uploading the video file instead."

---

# 18. Testing Strategy (FYP scope)

* **Unit tests**: concept-ranking scorer, schema validators, layout template functions
* **Integration tests**: generation pipeline end-to-end on 2–3 fixed sample videos (mock the LLM/image calls in CI, run real calls locally for the demo)
* **Manual E2E**: signup → create project → generate → view pages → export PDF, run before every major report checkpoint

---

# 19. AI Evaluation (this is your Results chapter — expand it)

Build a small fixed evaluation set:

```text
9–15 educational videos, e.g.:
3 programming
3 networking or DBMS
3 machine learning
```

For each, manually score:

* **Accuracy** — does generated content match the source? (spot-check against transcript)
* **Coverage** — were the important concepts captured?
* **Readability** — can a student actually read the generated page?
* **Hallucination rate** — did the system invent anything not in the source?

Report these as a table with actual numbers per video and an average — this is the strongest evidence of a "real" evaluation for the viva, far more convincing than a demo alone.

---

# 20. Caching (keep — cheap to implement, good cost story)

Cache transcript, concept extraction, and visual plans per project. If the user regenerates a page, do not re-run transcription or concept extraction — only re-run layout/image generation for that page.

---

# 21. Cost Control

* Concept importance threshold (§8 Stage 4) — don't generate visuals for everything
* Cache reuse (§20)
* Use a cheaper/smaller LLM for concept extraction where possible, reserve the stronger model for visual planning if quality differs noticeably
* Hard cap on video duration and page count per generation for the demo environment

---

# 22. Local Development

```bash
docker compose up -d        # postgres, redis (if used)
cd apps/api && pip install -r requirements.txt
uvicorn app.main:app --reload
cd apps/web && npm install && npm run dev
```

---

# 23. Environment Variables

```env
DATABASE_URL=
REDIS_URL=

AUTH_SECRET=

STORAGE_ENDPOINT=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
STORAGE_BUCKET=

LLM_API_KEY=
IMAGE_MODEL_API_KEY=
YOUTUBE_DATA_API_KEY=
```

Never commit `.env`; ship `.env.example` instead.

---

# 24. Development Phases (FYP timeline)

```text
Phase 1  Foundation           — repo, Next.js, FastAPI, Postgres, Docker
Phase 2  Authentication       — signup/login, protected routes
Phase 3  Dashboard + Create   — project list, create-project form
Phase 4  Source Ingestion     — YouTube captions path + file upload + STT path
Phase 5  Content Understanding — transcript → concepts (Prompts A, B)
Phase 6  Visual Planning       — Prompt C → visual_plans
Phase 7  Layout Rendering      — the 6 deterministic templates (§10)
Phase 8  Image Generation Layer — decorative-only compositing
Phase 9  Notebook Viewer + Regenerate
Phase 10 PDF Export
Phase 11 Evaluation            — run the fixed eval set (§19), collect results
Phase 12 Report + Polish
```

Suggested rough duration: 10–14 weeks depending on team size, consistent with a typical two-semester FYP timeline. Phases 7–8 (the hybrid rendering pipeline) are the technical core and deserve the most buffer time.

---

# 25. MVP Priority Matrix

## P0 — Must work for the project to be considered complete
```text
Authentication
YouTube caption ingestion + file upload/STT ingestion
Concept extraction + ranking
Visual planning
Deterministic layout rendering (6 templates)
Handwritten decorative layer
Notebook viewer
PDF export
Evaluation results (§19)
```

## P1 — Implement if time remains
```text
Page regeneration
Second visual style (e.g. Clean Academic)
Simple AI chat grounded in the transcript
```

## P2 — Explicitly out of scope, report as Future Work only
```text
Billing/subscriptions
Credit system
Mind maps beyond the basic template
Browser extension
Mobile app
Multi-language support
Creator/social-media mode
```

---

# 26. First Technical Prototype (build this first, always)

```text
YouTube (captions) or uploaded video/audio
       ↓
Transcript
       ↓
Concept extraction + ranking (top ~5)
       ↓
Visual plans
       ↓
5 deterministically-rendered visual pages
       ↓
PDF
```

Get this working end-to-end on 2–3 real videos before building authentication, the dashboard, or any other SaaS scaffolding around it. This was correct in the original spec (§74/§75) and remains the single most important sequencing decision for the project.

---

# 27. Key Architectural Decision (unchanged — this is the project's thesis)

The system is **not**:
```text
VIDEO → LLM → IMAGE GENERATOR
```

It **is**:
```text
VIDEO → TRANSCRIPT → CONTENT MODEL → CONCEPT MODEL →
VISUAL PLAN → LAYOUT MODEL (deterministic) → RENDERING →
[optional VALIDATION] → FINAL PAGE
```

This should be stated explicitly and diagrammed in the report — it is the answer to "why is your project more than a wrapper around an image-generation API," which is a very likely viva question.

# End of PWD (FYP Edition)
