from typing import Literal

from pydantic import BaseModel

Tier = Literal["Strong", "Moderate", "Needs Work"]


class CriterionEvidence(BaseModel):
    """Evidence assessment for a single O-1A criterion."""

    name: str
    description: str
    met: bool
    evidence: str | None = None
    reasoning: str | None = None


class O1Assessment(BaseModel):
    """Complete O-1A assessment from LLM."""

    criteria: list[CriterionEvidence]
    score: int = 0  # Number of criteria met (0-8)
    tier: Tier = "Needs Work"  # Strength classification


class ChatMessage(BaseModel):
    """Single message in challenge chat."""

    role: Literal["user", "assistant"]
    content: str


class ChallengeSession(BaseModel):
    """State for a criterion challenge conversation."""

    criterion_name: str
    messages: list[ChatMessage] = []
