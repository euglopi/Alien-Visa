# System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                            │
│                   (Jinja Templates)                     │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────┐
│                    FastAPI                              │
│  ┌─────────────┬─────────────┬─────────────────────┐   │
│  │   Routes    │  Services   │   Templates         │   │
│  │  /upload    │  Parser     │   base.html         │   │
│  │  /analyze   │  Analyzer   │   upload.html       │   │
│  │  /interview │  Scorer     │   results.html      │   │
│  │  /results   │  Recommender│   interview.html    │   │
│  └─────────────┴─────────────┴─────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 External Services                        │
│  ┌─────────────────┐  ┌─────────────────────────────┐   │
│  │   docling.ai    │  │   LLM API (Claude/OpenAI)   │   │
│  │  Resume Parsing │  │   Gap Interview / Analysis  │   │
│  └─────────────────┘  └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI |
| Templating | Jinja2 |
| Styling | Tailwind CSS (via CDN) |
| Resume Parsing | docling |
| LLM | OpenAI API (via openai SDK) |
| Data Validation | Pydantic |
| Session Storage | In-memory dict (MVP) |
| JSON Handling | orjson |

## Project Structure

```
alien/
├── main.py                 # FastAPI app entry point
├── pyproject.toml
├── templates/
│   ├── base.html           # Base layout
│   ├── index.html          # Landing / upload page
│   ├── analyzing.html      # Loading state
│   ├── interview.html      # Gap interview questions
│   └── results.html        # Score + action plan
├── static/
│   └── styles.css          # Custom styles (if needed)
├── services/
│   ├── __init__.py
│   ├── parser.py           # Resume parsing via docling
│   ├── analyzer.py         # Map resume → O-1 criteria
│   ├── scorer.py           # Calculate suitability score
│   └── recommender.py      # Generate action plan
├── models/
│   ├── __init__.py
│   ├── resume.py           # Pydantic models for parsed resume
│   ├── criteria.py         # O-1 criteria definitions
│   └── assessment.py       # Score + recommendations
├── routes/
│   ├── __init__.py
│   ├── upload.py           # POST /upload
│   ├── interview.py        # GET/POST /interview
│   └── results.py          # GET /results
└── docs/
    ├── 00-product.md
    └── 01-system-design.md
```

## Data Models

### ParsedResume

```python
class ParsedResume(BaseModel):
    name: str | None
    email: str | None
    publications: list[str]
    awards: list[str]
    press_mentions: list[str]
    memberships: list[str]
    jobs: list[JobEntry]
    patents: list[str]
    speaking_engagements: list[str]
    education: list[Education]
    raw_text: str
```

### O1Criteria

```python
class CriterionEvidence(BaseModel):
    criterion: str  # e.g., "awards", "judging"
    met: bool
    evidence: list[str]  # Supporting items from resume
    confidence: float  # 0.0 - 1.0

class O1Assessment(BaseModel):
    criteria: list[CriterionEvidence]  # 8 items
    criteria_met_count: int
    meets_threshold: bool  # True if >= 3
    overall_score: float  # 0-100
    strength: str  # "Strong" | "Moderate" | "Needs Work"
```

### ActionPlan

```python
class Recommendation(BaseModel):
    criterion: str
    priority: str  # "quick_win" | "medium_term" | "strategic"
    action: str
    rationale: str

class ActionPlan(BaseModel):
    recommendations: list[Recommendation]
    missing_criteria: list[str]
```

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Landing page with upload form |
| POST | `/upload` | Accept resume file, parse, redirect to interview |
| GET | `/interview/{session_id}` | Show gap interview questions |
| POST | `/interview/{session_id}` | Submit interview answers |
| GET | `/results/{session_id}` | Show score + action plan |

## Session Flow

```
1. User visits /
   └── Renders index.html with upload form

2. User uploads resume → POST /upload
   ├── Parse resume via docling
   ├── Run initial O-1 criteria analysis
   ├── Store in session (session_id → data)
   └── Redirect to /interview/{session_id}

3. User answers gap questions → POST /interview/{session_id}
   ├── Merge interview answers with parsed data
   ├── Re-run analysis with complete data
   ├── Generate score + action plan
   └── Redirect to /results/{session_id}

4. User views results at /results/{session_id}
   └── Renders results.html with score, criteria breakdown, recommendations
```

## Services

### parser.py
- Input: Uploaded file (PDF/DOCX)
- Process: Use docling to extract text and structure
- Output: `ParsedResume`

### analyzer.py
- Input: `ParsedResume` + interview answers
- Process: LLM call to map evidence → O-1 criteria
- Output: `O1Assessment`

### scorer.py
- Input: `O1Assessment`
- Process: Calculate weighted score, determine strength tier
- Output: Numeric score + tier label

### recommender.py
- Input: `O1Assessment`
- Process: For each unmet criterion, generate actionable recommendations
- Output: `ActionPlan`

## LLM Integration

Used for two purposes:

1. **Resume → Criteria Mapping**: Given parsed resume text, identify which O-1 criteria have supporting evidence
2. **Gap Interview Generation**: Based on missing criteria, generate targeted follow-up questions

Prompt templates stored as constants in `services/analyzer.py`.

## MVP Simplifications

- No database — in-memory session dict (lost on restart)
- No auth — sessions identified by UUID in URL
- No file storage — resume processed immediately, only extracted data kept
- Single-page interview — all gap questions on one page, not conversational
