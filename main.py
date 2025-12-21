from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from models.criteria import ChatMessage, ChallengeSession, CriterionEvidence, O1Assessment
from models.resume import ParsedResume
from services.analyzer import analyze_resume
from services.challenger import process_chat_message, rescore_criterion, start_challenge
from services.database import cache_result, get_cached_result, get_content_hash
from services.parser import parse_resume
from services.scorer import calculate_score


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str

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

    # Read file content and check cache
    content = await resume.read()
    content_hash = get_content_hash(content)

    cached = get_cached_result(content_hash)
    if cached:
        # Cache hit - use stored results
        sessions[session_id] = {
            "filename": resume.filename,
            "assessment": cached["assessment"],
            "parsed_resume": cached["parsed_resume"],
        }
    else:
        # Cache miss - parse and analyze
        parsed = await parse_resume(content, resume.filename)
        assessment = analyze_resume(parsed)

        parsed_dump = parsed.model_dump()
        assessment_dump = assessment.model_dump()

        # Store in cache for future uploads
        cache_result(content_hash, resume.filename, parsed_dump, assessment_dump)

        # Store session
        sessions[session_id] = {
            "filename": resume.filename,
            "assessment": assessment_dump,
            "parsed_resume": parsed_dump,
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

    assessment = O1Assessment(**session["assessment"])
    score, tier = calculate_score(assessment)
    parsed_resume = session.get("parsed_resume")

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "session_id": session_id,
            "criteria": assessment.criteria,
            "criteria_met": score,
            "tier": tier,
            "parsed_resume": parsed_resume,
        },
    )


def _get_session_and_criterion(
    session_id: str, criterion_name: str
) -> tuple[dict, CriterionEvidence]:
    """Helper to get session and criterion, raising 404 if not found."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    assessment = O1Assessment(**session["assessment"])
    criterion = next(
        (c for c in assessment.criteria if c.name == criterion_name), None
    )
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")

    return session, criterion


@app.post("/challenge/{session_id}/{criterion_name}/start")
async def challenge_start(session_id: str, criterion_name: str):
    """Start a challenge session for a specific criterion."""
    session, criterion = _get_session_and_criterion(session_id, criterion_name)

    # Initialize challenges dict if needed
    if "challenges" not in session:
        session["challenges"] = {}

    # Get resume text for context
    resume_text = session.get("parsed_resume", {}).get("raw_text", "")

    # Generate initial educational message
    initial_message = start_challenge(criterion, resume_text)

    # Create challenge session
    challenge = ChallengeSession(
        criterion_name=criterion_name,
        messages=[ChatMessage(role="assistant", content=initial_message)],
    )
    session["challenges"][criterion_name] = challenge.model_dump()

    return {
        "messages": [m.model_dump() for m in challenge.messages],
        "criterion": criterion.model_dump(),
    }


@app.post("/challenge/{session_id}/{criterion_name}/chat")
async def challenge_chat(session_id: str, criterion_name: str, body: ChatRequest):
    """Send a message in the challenge chat."""
    session, criterion = _get_session_and_criterion(session_id, criterion_name)

    # Get or create challenge session
    if "challenges" not in session or criterion_name not in session["challenges"]:
        raise HTTPException(
            status_code=400, detail="Challenge session not started. Call /start first."
        )

    challenge_data = session["challenges"][criterion_name]
    challenge = ChallengeSession(**challenge_data)

    # Get resume text for context
    resume_text = session.get("parsed_resume", {}).get("raw_text", "")

    # Process message and get response
    assistant_response = process_chat_message(
        challenge.messages, criterion, resume_text, body.message
    )

    # Update chat history
    challenge.messages.append(ChatMessage(role="user", content=body.message))
    challenge.messages.append(ChatMessage(role="assistant", content=assistant_response))
    session["challenges"][criterion_name] = challenge.model_dump()

    return {
        "messages": [m.model_dump() for m in challenge.messages],
        "assistant_message": assistant_response,
    }


@app.post("/challenge/{session_id}/{criterion_name}/rescore")
async def challenge_rescore(session_id: str, criterion_name: str):
    """Re-evaluate the criterion based on challenge conversation."""
    session, criterion = _get_session_and_criterion(session_id, criterion_name)

    # Ensure challenge session exists
    if "challenges" not in session or criterion_name not in session["challenges"]:
        raise HTTPException(
            status_code=400, detail="Challenge session not started. Call /start first."
        )

    challenge_data = session["challenges"][criterion_name]
    challenge = ChallengeSession(**challenge_data)

    # Get resume text for context
    resume_text = session.get("parsed_resume", {}).get("raw_text", "")

    # Rescore the criterion
    new_criterion = rescore_criterion(criterion, challenge.messages, resume_text)

    # Update the assessment in session
    assessment = O1Assessment(**session["assessment"])
    for i, c in enumerate(assessment.criteria):
        if c.name == criterion_name:
            assessment.criteria[i] = new_criterion
            break

    # Recalculate score and tier
    new_score, new_tier = calculate_score(assessment)
    assessment.score = new_score
    assessment.tier = new_tier
    session["assessment"] = assessment.model_dump()

    return {
        "success": True,
        "criterion": new_criterion.model_dump(),
        "new_score": new_score,
        "new_tier": new_tier,
    }
