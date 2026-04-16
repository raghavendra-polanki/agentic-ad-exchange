"""Matching engine schemas — relevance scoring and match results."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class MatchScore(BaseModel):
    """Individual agent's relevance score for an opportunity."""

    demand_agent_id: str
    organization: str
    relevance_score: float = 0.0  # 0-100 composite
    sport_match: float = 0.0
    reach_match: float = 0.0
    budget_match: float = 0.0
    format_match: float = 0.0
    conflict_status: str = "pending"  # cleared / blocked / pending
    reasoning: str = ""


class MatchResult(BaseModel):
    """Result of matching an opportunity against all demand agents."""

    opportunity_id: str
    scored_agents: list[MatchScore] = Field(default_factory=list)
    matched_agent_ids: list[str] = Field(default_factory=list)
    blocked_agent_ids: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
