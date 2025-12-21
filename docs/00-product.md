# O-1 Visa Readiness Analyzer

## Overview

A tool that evaluates a user's eligibility for an O-1 visa by analyzing their resume against the 8 evidentiary criteria, identifying gaps, and providing actionable recommendations to strengthen their application.

## Target Users

- Founders
- Engineers
- Researchers
- Other high-skilled professionals seeking O-1 "extraordinary ability" classification

## Core Value Proposition

1. **Clarity** — Demystify the vague "extraordinary ability" standard by mapping it to concrete, enumerable criteria
2. **Assessment** — Provide an honest evaluation of current O-1 readiness
3. **Action** — Generate a prioritized roadmap to close eligibility gaps

## User Flow

### Step 1: Resume Upload
- Drag-and-drop interface
- Parse resume using docling.ai

### Step 2: Resume Analysis
Extract structured data:
- Publications
- Awards
- Press/media mentions
- Salary information
- Job titles
- Professional memberships
- Speaking engagements
- Patents/original contributions

### Step 3: O-1 Criteria Mapping
Map extracted data to the 8 O-1 evidentiary categories:

| # | Criterion | Description |
|---|-----------|-------------|
| 1 | Awards | Nationally/internationally recognized prizes |
| 2 | Membership | Membership in associations requiring outstanding achievement |
| 3 | Published Material | Press about the applicant in professional publications |
| 4 | Judging | Participation as a judge of others' work |
| 5 | Original Contributions | Original scientific, scholarly, or business contributions of major significance |
| 6 | Scholarly Articles | Authorship of scholarly articles in professional journals |
| 7 | Employment in Critical Role | Employment in a critical or essential capacity at distinguished organizations |
| 8 | High Salary | Commanding a high salary or remuneration relative to others in the field |

**Requirement:** Applicant must satisfy at least 3 of 8 criteria.

### Step 4: Gap Interview
Chatbot asks targeted follow-up questions for missing evidence:
- "Have you judged others' work? (hiring panels, grant reviews, peer review)"
- "Have you been quoted or featured in any press coverage?"
- "Do you hold any patents or have documented original contributions?"

### Step 5: Suitability Score
Visual dashboard showing:
- Criteria met vs. missing (progress bar)
- Checklist of evidence by category
- Overall readiness assessment (e.g., "Strong", "Moderate", "Needs Work")

### Step 6: Action Plan
Prioritized recommendations to close gaps:
- Quick wins (evidence that may already exist but wasn't captured)
- Medium-term actions (e.g., submit to conferences, seek press coverage)
- Strategic investments (e.g., join selective professional associations)

## Future Roadmap (Out of Scope for MVP)

### Job/Opportunity Matcher
- Surface roles at cap-exempt organizations
- H-1B-friendly sponsor database
- Salary benchmarking data

## Technical Notes

- Resume parsing: docling.ai
- O-1 criteria rubric: hardcoded/static (criteria don't change)
- Gap interview: decision-tree flow (doesn't require full agentic behavior)
- Score visualization: progress bar + checklist

## Success Metrics

- User completes full assessment flow
- User receives actionable, personalized recommendations
- Clear visualization of current standing vs. requirements
