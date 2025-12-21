from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from models.criteria import ChatMessage, ChallengeSession, CriterionEvidence, O1Assessment
from models.network import MentorshipRequest
from models.resume import ParsedResume
from services.analyzer import analyze_resume
from services.challenger import process_chat_message, rescore_criterion, start_challenge
from services.database import cache_result, get_cached_result, get_content_hash
from services.network import NetworkService
from services.parser import parse_resume
from services.scorer import calculate_score


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str


class MentorshipRequestBody(BaseModel):
    """Request body for creating a mentorship request."""

    mentor_id: str
    session_id: str
    field: str
    message: str

app = FastAPI(title="O-1 Visa Readiness Analyzer")

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
network_service = NetworkService()

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
        return RedirectResponse(url="/", status_code=302)

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

    # Generate initial educational message and suggestions
    result = start_challenge(criterion, resume_text)
    initial_message = result["message"]
    suggestions = result["suggestions"]

    # Create challenge session
    challenge = ChallengeSession(
        criterion_name=criterion_name,
        messages=[ChatMessage(role="assistant", content=initial_message)],
    )
    session["challenges"][criterion_name] = challenge.model_dump()

    return {
        "messages": [m.model_dump() for m in challenge.messages],
        "criterion": criterion.model_dump(),
        "suggestions": suggestions,
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

    # Process message and get response with suggestions
    result = process_chat_message(
        challenge.messages, criterion, resume_text, body.message
    )
    assistant_response = result["message"]
    suggestions = result["suggestions"]

    # Update chat history
    challenge.messages.append(ChatMessage(role="user", content=body.message))
    challenge.messages.append(ChatMessage(role="assistant", content=assistant_response))
    session["challenges"][criterion_name] = challenge.model_dump()

    return {
        "messages": [m.model_dump() for m in challenge.messages],
        "assistant_message": assistant_response,
        "suggestions": suggestions,
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


# Network and Community Features
@app.get("/api/mentors")
async def get_mentors(field: str, subfield: str = None, limit: int = 5):
    """Find relevant mentors for a given field."""
    try:
        mentors = network_service.find_mentors(field, subfield, limit)
        return {"mentors": [m.model_dump() for m in mentors]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find mentors: {str(e)}")


@app.post("/api/mentorship-requests")
async def create_mentorship_request(body: MentorshipRequestBody):
    """Create a mentorship request tied to a resume session."""
    try:
        request_obj = MentorshipRequest(
            id=str(uuid4()),
            seeker_id=body.session_id,
            mentor_id=body.mentor_id,
            field=body.field,
            topics=["Resume review", "O-1 case strategy"],
            message=body.message,
        )
        network_service.request_mentorship(request_obj)
        return {"success": True}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create mentorship request: {str(e)}",
        )


@app.get("/api/experts")
async def get_experts(field: str, subfield: str = None, limit: int = 5):
    """Find relevant expert reviewers for consultation letters."""
    try:
        experts = network_service.find_experts(field, subfield, limit)
        return {"experts": [e.model_dump() for e in experts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find experts: {str(e)}")


@app.get("/api/success-stories")
async def get_success_stories(field: str = None, min_score: int = 0, limit: int = 10):
    """Get relevant success stories."""
    try:
        stories = network_service.get_success_stories(field, min_score, limit)
        return {"stories": [s.model_dump() for s in stories]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get success stories: {str(e)}")


@app.get("/api/forum-posts")
async def get_forum_posts(field: str = None, tag: str = None, limit: int = 20):
    """Get forum posts, optionally filtered by field or tag."""
    try:
        posts = network_service.get_forum_posts(field, tag, limit)
        return {"posts": [p.model_dump() for p in posts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forum posts: {str(e)}")


@app.post("/api/seed-sample-data")
async def seed_sample_data():
    """Seed sample data for development (admin only)."""
    try:
        network_service.seed_sample_data()
        return {"message": "Sample data seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed data: {str(e)}")


# Network pages
@app.get("/mentors")
async def mentors_page(request: Request):
    """Mentor matching page."""
    return templates.TemplateResponse(request, "mentors.html")


@app.get("/experts")
async def experts_page(request: Request):
    """Expert reviewer database page."""
    return templates.TemplateResponse(request, "experts.html")


@app.get("/community")
async def community_page(request: Request):
    """Community features page."""
    return templates.TemplateResponse(request, "community.html")
