from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from services.parser import parse_resume

app = FastAPI(title="O-1 Visa Readiness Analyzer")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# In-memory session store (lost on restart)
sessions: dict[str, dict] = {}

# Hardcoded O-1A criteria data
HARDCODED_CRITERIA = [
    {
        "name": "Awards",
        "description": "Nationally or internationally recognized prizes or awards for excellence",
        "met": True,
        "evidence": "Best Paper Award at International Conference on Machine Learning (2023)",
    },
    {
        "name": "Membership",
        "description": "Membership in associations requiring outstanding achievement",
        "met": True,
        "evidence": "Member of IEEE Senior Grade, requiring significant contributions to the field",
    },
    {
        "name": "Published Material",
        "description": "Published material in professional publications about the person's work",
        "met": True,
        "evidence": "Featured in TechCrunch and Wired for innovative AI research",
    },
    {
        "name": "Judging",
        "description": "Participation as a judge of the work of others in the field",
        "met": False,
        "evidence": None,
    },
    {
        "name": "Original Contributions",
        "description": "Original scientific, scholarly, or business-related contributions of major significance",
        "met": True,
        "evidence": "Developed novel algorithm adopted by 500+ companies worldwide",
    },
    {
        "name": "Scholarly Articles",
        "description": "Authorship of scholarly articles in professional journals or major media",
        "met": True,
        "evidence": "15 peer-reviewed publications with 2,000+ citations",
    },
    {
        "name": "Critical Employment",
        "description": "Employment in a critical or essential capacity at distinguished organizations",
        "met": False,
        "evidence": None,
    },
    {
        "name": "High Salary",
        "description": "High salary or remuneration compared to others in the field",
        "met": False,
        "evidence": None,
    },
]


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/upload")
async def upload(request: Request, resume: UploadFile):
    # Generate session ID
    session_id = str(uuid4())

    # Parse the uploaded file
    content = await resume.read()
    parsed = await parse_resume(content, resume.filename)

    # Store session with parsed resume and hardcoded criteria
    sessions[session_id] = {
        "filename": resume.filename,
        "criteria": HARDCODED_CRITERIA,
        "parsed_resume": parsed.model_dump(),
    }

    return RedirectResponse(url=f"/results/{session_id}", status_code=303)


@app.get("/results/{session_id}")
async def results(request: Request, session_id: str):
    session = sessions.get(session_id)
    if not session:
        return templates.TemplateResponse(
            request,
            "base.html",
            {"title": "Not Found"},
            status_code=404,
        )

    criteria = session["criteria"]
    criteria_met = sum(1 for c in criteria if c["met"])
    parsed_resume = session.get("parsed_resume")

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "criteria": criteria,
            "criteria_met": criteria_met,
            "parsed_resume": parsed_resume,
        },
    )
