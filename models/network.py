from typing import List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime


class MentorProfile(BaseModel):
    """Profile of a successful O-1 holder willing to mentor."""

    id: str
    name: str  # Anonymous or real name with permission
    field: str  # e.g., "Computer Science", "Medicine", "Arts"
    subfield: Optional[str] = None  # e.g., "AI/ML", "Cardiology", "Digital Arts"
    years_experience: int
    o1_approval_year: int
    location: str  # City, Country
    languages: List[str] = ["English"]
    availability: Literal["high", "medium", "low"] = "medium"
    mentoring_topics: List[str]  # What they can help with
    contact_method: Literal["email", "linkedin", "platform"] = "platform"
    created_at: datetime
    is_active: bool = True


class ExpertReviewer(BaseModel):
    """Expert available to provide consultation letters."""

    id: str
    name: str
    credentials: str  # e.g., "Professor of Computer Science, Stanford University"
    field: str
    subfield: Optional[str] = None
    institution: str
    position: str
    publications: Optional[int] = None
    years_experience: int
    consultation_fee_range: str  # e.g., "$500-2000"
    response_time: str  # e.g., "1-2 weeks"
    contact_info: str  # How to reach them
    verified: bool = False  # USCIS verification or similar
    rating: Optional[float] = None  # Average rating from past consultations
    review_count: int = 0
    created_at: datetime
    is_active: bool = True


class SuccessStory(BaseModel):
    """Anonymous success story from approved O-1 applicant."""

    id: str
    field: str
    subfield: Optional[str] = None
    approval_timeline: str  # e.g., "8 months"
    key_success_factors: List[str]
    challenges_overcome: List[str]
    advice_for_others: str
    criteria_met: List[str]  # Which O-1 criteria they satisfied
    assessment_score: int  # Their final score 0-8
    approval_year: int
    created_at: datetime
    helpful_votes: int = 0


class ForumPost(BaseModel):
    """Community forum post."""

    id: str
    author_id: str  # Anonymous user ID
    field: str
    subfield: Optional[str] = None
    title: str
    content: str
    tags: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    reply_count: int = 0
    helpful_votes: int = 0
    is_resolved: bool = False


class ForumReply(BaseModel):
    """Reply to a forum post."""

    id: str
    post_id: str
    author_id: str
    content: str
    created_at: datetime
    helpful_votes: int = 0
    is_expert_answer: bool = False


class MentorshipRequest(BaseModel):
    """Request for mentorship."""

    id: str
    seeker_id: str
    mentor_id: str
    field: str
    topics: List[str]
    message: str
    status: Literal["pending", "accepted", "declined", "completed"] = "pending"
    created_at: datetime
    responded_at: Optional[datetime] = None


class NetworkMatch(BaseModel):
    """Matching result for mentors or experts."""

    type: Literal["mentor", "expert"]
    id: str
    name: str
    field: str
    relevance_score: float  # 0-1, how well they match
    key_qualifications: List[str]
    availability: Optional[str] = None
    contact_info: Optional[str] = None
