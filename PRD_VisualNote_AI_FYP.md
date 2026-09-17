# Product Requirements Document (PRD)

## VisualNote AI — AI-Powered Video-to-Visual Learning Platform (Final Year Project Edition)

**Version:** 2.0 (FYP-scoped)
**Status:** Development Ready
**Product Type:** AI web application / EdTech
**Primary Users:** College students, self-learners
**Platform:** Web application (desktop/tablet-first; mobile out of scope)

> **Scope note:** This edition trims the original product vision down to what a final-year project team can realistically build, test, and evaluate in one project cycle, while keeping the broader vision documented as Future Scope (§16) so the report can still argue the idea's larger potential.

---

# 1. Product Overview

## 1.1 Product Name
VisualNote AI

## Tagline
Turn videos into visual knowledge.

## Product Description
VisualNote AI converts educational videos (YouTube or user-uploaded) into structured, visually organized study notes — handwritten-style pages combining explanations, diagrams, and key facts — rather than a plain text summary.

Core pipeline:
```text
Video
  ↓
Transcript (captions or speech-to-text)
  ↓
AI Concept Extraction + Ranking
  ↓
Visual Planning
  ↓
Deterministic Layout Rendering + Illustrative AI Imagery
  ↓
Visual Notebook (viewable pages)
  ↓
PDF Export
```

---

# 2. Problem Statement

1. Important information from lecture videos is hard to revisit later.
2. Manual note-taking while watching is effortful and lossy.
3. Long videos contain a lot of low-value content mixed with the important parts.
4. Existing AI video summarizers are almost entirely text-based.
5. Technical concepts (processes, comparisons, architectures) are often genuinely easier to understand visually than as prose.
6. Turning a lecture into exam-ready revision material still requires manual effort even after a text summary exists.
7. Hand-drawing diagrams or handwritten-style notes for revision is time-consuming.

VisualNote AI addresses this by automatically converting video content into visual, revision-ready study pages.

---

# 3. Product Vision

**Long-term:** an AI learning engine that converts any educational content (video, audio, PDF, articles) into the most effective visual representation for understanding and revision, with practice material layered on top.

**This project's scope:** the video-to-visual-notes core only. Everything downstream (multi-format ingestion, quizzes, flashcards, creator tools) is documented as future direction, not built.

---

# 4. Product Goals (FYP scope)

| Goal | Description |
|---|---|
| G1 — Video Understanding | Extract the important concepts from a video's transcript |
| G2 — Automatic Note Generation | No manual transcription or note-taking required |
| G3 — Visual Representation | Map each concept to an appropriate visual type (flowchart, comparison table, formula block, etc.) |
| G4 — Handwritten-Style Output | Generate one convincing, consistent visual style (handwritten) rather than several partial ones |
| G5 — Accuracy Over Decoration | Factual text must always be correct and legible — this takes priority over visual polish |
| G6 — Export | Users can download the generated notebook as a PDF |
| G7 — Basic Personalization | Users can choose a learning mode that controls depth/length (see §8) |

Dropped from the original goal list for this scope: full personalized-learning controls, AI chat as a core goal (moved to stretch), complete "study pack" generation (quizzes/flashcards — stretch goal only).

---

# 5. Non-Goals

The project will **not**:

* download or redistribute YouTube video/audio files (captions-only ingestion — see PWD §8 Stage 2)
* generate unlimited pages per video (page count is capped and driven by concept importance ranking)
* support every visual style from the original vision (ships with one: Handwritten)
* build a mobile app or browser extension
* implement billing or a credit-purchase system
* support multiple languages
* provide real-time collaboration

---

# 6. Target Users

**Primary: college students** studying technical subjects from recorded lectures or YouTube tutorials — Computer Science, IT, Engineering, and similar technical programs are the best fit because their content (processes, comparisons, architectures, formulas) visualizes well.

## Persona — Engineering Student ("Rahul")
Watches DBMS, OS, Computer Networks, and ML lecture videos.
> "I understand the lecture while watching, but later I can't find where a specific concept was explained."

Needs: visual notes, diagrams, quick revision material tied back to the source timestamp.

---

# 7. Core User Journey (FYP scope)

```text
Landing / Login
     ↓
Sign Up / Login
     ↓
Dashboard
     ↓
Create Project → paste YouTube URL OR upload video/audio
     ↓
Configure: Learning Mode
     ↓
Generation (with real progress states)
     ↓
Visual Notebook (page viewer)
     ↓
Regenerate individual pages (if implemented)
     ↓
Export PDF
```

Removed for FYP: style switching mid-journey (only one style exists), study-pack generation, AI chat (unless built as a stretch goal, in which case it can be inserted after the notebook step).

---

# 8. Input Types

**YouTube URL** — processed via the YouTube Data API captions endpoint only. If a video has no captions, the app rejects it with a clear message directing the user to upload the file instead. (See PWD §8 for the reasoning — this boundary matters for scope and for ToS compliance.)

**Uploaded video/audio** — MP4, MOV, WebM (video); MP3, WAV, M4A (audio) if audio-only upload is supported. Processed via local speech-to-text (e.g. Whisper).

---

# 9. Output

**Visual Notes** — one style for MVP: **Handwritten**. Each page contains a title, concise explanation, and one visual element (diagram, comparison table, formula block, timeline, or concept map) drawn from a fixed set of six deterministic layout templates (see PWD §10).

Every page retains a link back to its source timestamp range in the original video where possible.

**PDF Export** — cover page, table of contents, the generated pages, and a short source-attribution page (video title + link).

Dropped for MVP: PNG-only export, image collections, shareable links, multiple simultaneous styles per project.

---

# 10. Intelligent Visual Selection

The system automatically assigns each concept a visual type, using a fixed mapping (matches PWD §10's six templates):

| Concept type | Visual type |
|---|---|
| Definition | Concept card |
| Process | Flowchart |
| Comparison | Comparison table |
| Formula | Formula block |
| Relationship | Concept map |
| Sequence/history | Timeline |

Example — "TCP vs UDP" produces:
```text
Page 1  Introduction
Page 2  TCP — flowchart
Page 3  UDP — flowchart
Page 4  TCP vs UDP — comparison table
Page 5  Exam revision summary
```

---

# 11. Learning Modes

Replaces the original's separate "output mode" + "page count" selectors with one control, matching PWD §5's `learning_mode` field:

| Mode | Target page count | Content |
|---|---|---|
| Quick | 3–5 | Only the highest-importance concepts |
| Standard | 6–10 | Concepts + examples |
| Detailed | 10–15 | Comprehensive coverage |
| Exam | 5–8 | Definitions, formulas, comparison pages, revision summary — biased toward high-yield content |

Dropped "Beginner" as a separate mode for MVP — folding "simpler language" into a single explicit toggle (Beginner language: on/off) alongside mode selection is simpler to implement than a fifth full mode; add it back only if time remains.

---

# 12. Dashboard (FYP scope)

```text
Welcome back

[ Create New Visual Notes ]

Recent Projects
  Machine Learning         ██████████ 100%
  Computer Networks        ██████████ 100%
  DBMS Lecture              ██████░░░░ 60%
```

Dropped: usage/credit counters (no billing in MVP), project filters/search (add only if project count in demo data justifies it).

---

# 13. Create Project Screen

```text
Create Visual Notes

[ YouTube URL ]   or   [ Upload Video/Audio ]

Learning Mode
○ Quick   ○ Standard   ○ Detailed   ○ Exam

[ Generate Visual Notes ]
```

Dropped: separate Learning Level selector, Style selector (only one style exists), Advanced Options panel.

---

# 14. Processing Experience

Show real progress states, not a generic spinner — this is cheap to implement and makes a strong impression in a live demo:

```text
Analyzing video...

✓ Transcript retrieved
✓ Topics detected
✓ Important concepts extracted
✓ Visual pages planned
● Generating visual pages (3 / 6)
○ Preparing PDF
```

---

# 15. Visual Notebook / Page Actions

```text
┌──────────────────────────────────────┐
│ VisualNote AI                Export  │
├─────────────┬────────────────────────┤
│ Pages       │                        │
│ 01          │     Generated Page     │
│ 02          │                        │
│ 03          │        IMAGE           │
│ 04          │                        │
├─────────────┴────────────────────────┤
│         Regenerate  |  Download      │
└──────────────────────────────────────┘
```

Page actions for MVP: **Regenerate**, **Download (PDF)**. Simplify / Make Detailed / Change Style / Convert to Diagram / Edit Text / Duplicate are all stretch goals — each implies non-trivial pipeline branches and should only be added once the core P0 pipeline (PWD §25) is solid.

---

# 16. Future Scope (explicitly not built — for the report's "Future Work" chapter)

Kept from the original vision to show the idea's full potential without inflating build scope:

* Additional visual styles: Clean Academic, Infographic, Blackboard, full Mind Map
* AI chat grounded in project content
* Quizzes, flashcards, full "study pack" generation
* Multi-language support
* Browser extension, mobile app
* Creator mode / social-media card generation
* Subscription billing and credit system
* Collaborative/classroom workspaces
* Public API / LMS integration

```text
                    VISUALNOTE AI (long-term)
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       LEARN           CREATE         REVISE
          │              │              │
      Videos          Carousels       Flashcards
      Audio           Infographics    Quizzes
      PDFs            Posts           Questions
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  KNOWLEDGE SYSTEM
```

---

# 17. Accuracy Requirement (state this explicitly in the report)

VisualNote AI prioritizes correctness over visual polish. Source facts and visual presentation are architecturally separated: the LLM produces structured facts (PWD §6 Concept JSON); a deterministic layout engine renders that text exactly; the image-generation model only supplies decorative/illustrative elements and never sees raw factual content to "render as text." This is the project's core design decision — see PWD §27.

---

# 18. Authentication

Google OAuth and/or email/password. GitHub/Apple sign-in are future scope, not needed for a demo.

---

# 19. Privacy

Users can delete their own projects, which cascades to delete associated transcripts, generated pages, and exports. Uploaded video/audio files should not be retained indefinitely — delete the raw source file once transcription is complete, keeping only the transcript (this also reduces storage cost, which matters for a self-funded student project).

---

# 20. Copyright / Safety Considerations

* The product is not a YouTube downloader — no video or audio stream is ever fetched from YouTube; only the official captions endpoint is used.
* Every generated notebook retains a link back to the source video.
* User-uploaded content is processed according to the app's own terms/privacy policy, which the report should briefly state even in placeholder form (a real deployment would need this; a project report should at least acknowledge it).

---

# 21. MVP Requirements (must have)

* Authentication
* Dashboard + project list
* YouTube URL input (captions-based) and file upload (STT-based)
* Transcript processing
* Concept extraction + importance ranking
* Visual planning
* Deterministic layout rendering (six templates)
* Handwritten decorative image layer
* Notebook page viewer
* Page regeneration
* PDF export
* Evaluation results against a fixed test set (this belongs in "requirements," not just "nice to have" — it is what makes the project defensible as more than a demo)

---

# 22. Should Have (implement if time remains)

* Second visual style
* Simple AI chat grounded in transcript
* Timestamp deep-linking back into an embedded video player

---

# 23. Success Metrics (for evaluation, scaled to a project — not a company)

| Metric | Target | How to measure |
|---|---|---|
| Generation completion rate | ≥ 90% on the fixed eval set | % of test videos that produce a complete notebook without failure |
| Factual accuracy | Manually scored against transcript | See PWD §19 |
| Concept coverage | Manually scored | See PWD §19 |
| Readability | Manually scored (can also collect a few outside testers' ratings) | Simple 1–5 rubric |
| Export success | 100% of completed projects can export a PDF | Functional test |

Dropped the original's business metrics (activation %, retention %, satisfaction survey targets) — these belong to a live product with real users over time, not a project evaluated once at submission. Keep a short "if this were a live product" paragraph in Future Work instead if the report wants to gesture at them.

---

# 24. Product Principle

> Don't summarize everything. Visualize what matters.

This stays unchanged from the original — it's a strong, one-line articulation of the project's thesis and works well as an opening line for the report's Introduction.

---

# 25. Definition of Done (FYP)

A user can:

1. Sign up / log in.
2. Paste a YouTube URL with captions, or upload a video/audio file.
3. Select a Learning Mode.
4. Start generation and see real progress states.
5. Receive a set of structured visual pages (deterministic text + illustrative imagery).
6. Browse pages in the notebook viewer.
7. Regenerate an individual page.
8. Download the notebook as a PDF.
9. Return to the project later from the dashboard.

And separately, for the report:

10. A fixed evaluation set (9–15 videos) has been run through the pipeline with accuracy/coverage/readability/hallucination scores recorded and presented as results.

If 1–9 work reliably and 10 has been completed, the project is done.

# End of PRD (FYP Edition)
