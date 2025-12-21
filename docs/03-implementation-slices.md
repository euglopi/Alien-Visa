# O-1 Visa Readiness Analyzer - Vertical Slices

## Current State
- Empty project with placeholder `main.py`
- No dependencies configured
- Full design docs exist in `docs/`

## Approach
Each slice delivers working end-to-end functionality. Ship each slice before starting the next.

---

## Slice 0: Project Skeleton
**Goal:** FastAPI app running with basic structure

- [ ] Add dependencies to `pyproject.toml`: fastapi, uvicorn, jinja2, python-multipart, pydantic, orjson, openai, docling
- [ ] Create folder structure: `templates/`, `services/`, `models/`, `routes/`
- [ ] Basic FastAPI app in `main.py` with Jinja2 configured
- [ ] `templates/base.html` with Tailwind CDN
- [ ] `GET /` returns "Hello World" page
- [ ] Verify: `uvicorn main:app --reload` works

**Files:** `main.py`, `pyproject.toml`, `templates/base.html`

---

## Slice 1: Upload Flow (Hardcoded)
**Goal:** Complete user flow with fake data

- [ ] `templates/index.html` - landing page with file upload form
- [ ] `POST /upload` - accept file, generate session ID, redirect
- [ ] `templates/results.html` - display hardcoded O-1 criteria results
- [ ] `GET /results/{session_id}` - render hardcoded results
- [ ] In-memory session store (dict)

**Files:** `main.py`, `templates/index.html`, `templates/results.html`

---

## Slice 2: Resume Parsing
**Goal:** Extract real data from uploaded resume

- [ ] `services/parser.py` - use docling to parse PDF/DOCX
- [ ] `models/resume.py` - `ParsedResume` Pydantic model
- [ ] Update `/upload` to parse file and store extracted data
- [ ] Display raw parsed text on results page (debug view)

**Files:** `services/parser.py`, `models/resume.py`, `main.py`

---

## Slice 3: O-1 Criteria Mapping
**Goal:** LLM analyzes resume against 8 criteria

- [ ] `models/criteria.py` - `CriterionEvidence`, `O1Assessment` models
- [ ] `services/analyzer.py` - OpenAI call to map resume → criteria
- [ ] Prompt template using exact regulatory language from `docs/02-o1a-criteria.md`
- [ ] Update results page to show criteria breakdown (met/not met + evidence)

**Files:** `services/analyzer.py`, `models/criteria.py`, `templates/results.html`

---

## Slice 4: Scoring & Dashboard
**Goal:** Visual assessment of O-1 readiness

- [ ] `services/scorer.py` - calculate score, determine strength tier
- [ ] Update `O1Assessment` with score fields
- [ ] Results page: progress bar (X/8 criteria), checklist, tier badge
- [ ] Color coding: Strong (green), Moderate (yellow), Needs Work (red)

**Files:** `services/scorer.py`, `templates/results.html`

---

## Slice 5: Gap Interview
**Goal:** Collect additional evidence through targeted questions

- [ ] `templates/interview.html` - form with questions for missing criteria
- [ ] `GET /interview/{session_id}` - show questions based on gaps
- [ ] `POST /interview/{session_id}` - save answers, re-run analysis
- [ ] Update flow: upload → interview → results
- [ ] Decision tree for questions (not full LLM, just targeted prompts)

**Files:** `templates/interview.html`, `routes/interview.py`

---

## Slice 6: Action Plan
**Goal:** Actionable recommendations to close gaps

- [ ] `models/assessment.py` - `Recommendation`, `ActionPlan` models
- [ ] `services/recommender.py` - generate recommendations per unmet criterion
- [ ] Categorize: quick wins, medium-term, strategic
- [ ] Final results page with full report: score + criteria + action plan

**Files:** `services/recommender.py`, `models/assessment.py`, `templates/results.html`

---

## File Structure (Final)
```
alien/
├── main.py
├── pyproject.toml
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── interview.html
│   └── results.html
├── services/
│   ├── parser.py
│   ├── analyzer.py
│   ├── scorer.py
│   └── recommender.py
├── models/
│   ├── resume.py
│   ├── criteria.py
│   └── assessment.py
└── docs/
    ├── 00-product.md
    ├── 01-system-design.md
    ├── 02-o1a-criteria.md
    └── 03-implementation-slices.md
```

---

## Notes
- Use `orjson` instead of `json` per project guidelines
- OpenAI API key via environment variable
- No database - in-memory sessions (lost on restart)
- Tailwind CSS via CDN (no build step)
