from typing import Literal

from models.criteria import O1Assessment

Tier = Literal["Strong", "Moderate", "Needs Work"]


def calculate_score(assessment: O1Assessment) -> tuple[int, Tier]:
    """Calculate score (criteria met count) and determine strength tier.

    Args:
        assessment: The O-1A assessment with criteria results

    Returns:
        Tuple of (score, tier) where score is 0-8 and tier is the strength level
    """
    criteria_met = sum(1 for c in assessment.criteria if c.met)

    # Tier thresholds based on O-1A requirements (need 3 of 8 to qualify)
    if criteria_met >= 5:
        tier: Tier = "Strong"
    elif criteria_met >= 3:
        tier = "Moderate"
    else:
        tier = "Needs Work"

    return criteria_met, tier
