# VisualNote AI — System Architecture Document

## Overview
VisualNote AI is a video-to-visual learning platform designed to transform lectures and educational videos into structured, revision-ready visual notes, diagrams, formula blocks, and concept maps.

---

## 1. System Topology

```text
               ┌──────────────────────────────┐
               │    Next.js 14 Web Client     │
               │   (App Router, TypeScript)   │
               └──────────────┬───────────────┘
                              │ HTTPS / REST
                              ▼
               ┌──────────────────────────────┐
               │       FastAPI Backend        │
               │     (Python 3.11 / Async)    │
               └───────┬──────────────┬───────┘
                       │              │
         ┌─────────────┴──────┐ ┌─────┴────────────────┐
         │   PostgreSQL 15    │ │       Redis 7        │
         │ (SQLAlchemy Models)│ │(Queue/Job Management)│
         └────────────────────┘ └──────────────────────┘
```

---

## 2. The Core Architectural Thesis

### What VisualNote AI is NOT:
```text
Video ──> LLM ──> Image Generator (generating hallucinated text) ──> Broken Notes
```

### What VisualNote AI IS:
```text
Video / Audio Source
      │
      ▼
Transcript Extraction (Timedtext API or Whisper STT)
      │
      ▼
Content Understanding & Concept Extraction (Structured JSON)
      │
      ▼
Concept Ranking (Importance Scorer: 0.0 – 1.0)
      │
      ▼
Visual Planning (Deterministic Layout Assignment)
      │
      ▼
Deterministic Layout Rendering (HTML/CSS/KaTeX/SVG ──> Exact High-Res Text)
      │
      ▼
Decorative / Illustrative AI Layer (Paper textures, subtle accents — NO TEXT)
      │
      ▼
Image Compositing (PIL / Headless Chromium)
      │
      ▼
Visual Notebook & Multi-Page PDF Export
```

---

## 3. Database Schema Entities

All entities are mapped with UUID primary keys and timezone-aware timestamps:

1. **User**: Account credentials, email uniqueness.
2. **Project**: Core workspace holding source type, configuration (`learning_level`, `output_mode`, `visual_style`), and lifecycle state.
3. **Source**: Raw input media tracking, mime types, duration, and storage keys.
4. **Transcript**: Raw language, full content, and timestamped segments (`[{start, end, text}]`).
5. **Concept**: Extracted educational units conforming to the canonical `ConceptJSON` schema with `importance_score` (0.0 to 1.0) and source time-ranges.
6. **VisualPlan**: 1:1 mapping from concept to one of 6 visual templates (`concept_card`, `flowchart`, `comparison_table`, `formula_block`, `timeline`, `concept_map`).
7. **Page**: Rendered visual note page with page number, image URL, and deterministic content snapshot.
8. **GenerationJob**: Asynchronous task status tracker (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`).
9. **Export**: Compiled artifact outputs (`PDF`, `PNG`).

---

## 4. Storage Abstraction
A modular `StorageService` interface separates business logic from local disk, MinIO, or AWS S3 buckets:
- `save(key, data, content_type)`
- `get(key)`
- `delete(key)`
- `exists(key)`
- `get_url(key)`
