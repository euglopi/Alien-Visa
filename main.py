from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from services.analyzer import analyze_resume
from services.parser import parse_resume

app = FastAPI(title="O-1 Visa Readiness Analyzer")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# In-memory session store (lost on restart)
sessions: dict[str, dict] = {}


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

    # Analyze resume against O-1A criteria
    assessment = analyze_resume(parsed)

    # Store session with parsed resume and assessment
    sessions[session_id] = {
        "filename": resume.filename,
        "assessment": assessment.model_dump(),
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

    assessment = session["assessment"]
    criteria = assessment["criteria"]
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
