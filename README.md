# O-1 Visa Readiness Analyzer

![Cover](assets/icon3.png)

An AI-powered tool that evaluates eligibility for O-1 visas by analyzing resumes against the 8 evidentiary criteria required for "extraordinary ability" classification.

## Features

- **Resume Upload & Analysis**: Upload your resume (PDF/DOCX) for comprehensive O-1A evaluation
- **AI-Powered Assessment**: Uses advanced AI to analyze your qualifications against exact USCIS criteria
- **Evidence-Based Results**: Provides specific evidence from your resume for each criterion
- **Visual Dashboard**: See your progress with clear visualizations and checklists
- **Action Planning**: Get prioritized recommendations to strengthen your O-1 application

## O-1A Criteria Evaluated

The tool assesses your resume against all 8 USCIS O-1A evidentiary criteria:

1. **Awards** - Nationally or internationally recognized prizes
2. **Membership** - Associations requiring outstanding achievements
3. **Published Material** - Press coverage in professional publications
4. **Judging** - Participation as a judge of others' work
5. **Original Contributions** - Major scientific/scholarly/business contributions
6. **Scholarly Articles** - Authorship in professional journals
7. **Critical Employment** - Essential roles at distinguished organizations
8. **High Salary** - Commanding high remuneration in your field

**Requirement**: Must satisfy at least 3 of 8 criteria.

## Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API key

### Installation
```bash
# Clone the repository
git clone https://github.com/adagradschool/alien.git
cd alien

# Install dependencies
pip install -r requirements.txt
# or using uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
