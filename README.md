# O-1 Visa Readiness Analyzer

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
```

### Running the Application
```bash
# Using uv
uv run uvicorn main:app --reload

# Or using python directly
python main.py
```

Open http://localhost:8000 in your browser.

## Usage

1. **Upload Resume**: Drag and drop your resume (PDF or DOCX format)
2. **AI Analysis**: The system parses and analyzes your resume against O-1A criteria
3. **Review Results**: See which criteria you meet with specific evidence
4. **Get Recommendations**: Receive actionable steps to strengthen your application

## Project Structure

```
alien/
├── main.py                 # FastAPI application
├── models/
│   ├── criteria.py        # O-1A criteria models
│   └── resume.py          # Resume parsing models
├── services/
│   ├── analyzer.py        # AI analysis service
│   ├── parser.py          # Resume parsing service
│   ├── scorer.py          # Scoring calculations
│   └── challenger.py      # Gap analysis
├── templates/
│   ├── base.html          # Base template
│   ├── index.html         # Upload page
│   └── results.html       # Results dashboard
├── docs/                  # Documentation
└── pyproject.toml         # Project configuration
```

## Technical Details

- **Backend**: FastAPI with async support
- **AI**: OpenAI GPT-4 for criteria analysis
- **Parsing**: Advanced document parsing for PDF/DOCX
- **Frontend**: Jinja2 templates with Tailwind CSS
- **Data Models**: Pydantic for type safety

## Contributing

This project is part of the `adagradschool/alien` initiative. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add license information here]

## Disclaimer

This tool provides general analysis based on USCIS O-1A criteria but does not constitute legal advice. Always consult with qualified immigration attorneys for your specific situation.
