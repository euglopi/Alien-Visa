from pydantic import BaseModel


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
