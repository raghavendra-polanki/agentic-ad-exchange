"""Matching engine — deterministic relevance scoring for demand agents.

Scores each demand agent against an opportunity across 4 factors (0-25 each = 0-100 total):
  - Sport match: does the agent's standing queries include this sport?
  - Reach match: projected reach vs agent's min_reach requirement
  - Budget match: agent's budget vs opportunity min_price
  - Format match: overlap between available formats and desired formats
"""

from src.schemas.agents import DemandAgentProfile
from src.schemas.matching import MatchResult, MatchScore
from src.schemas.opportunities import OpportunityRecord

# Threshold: agents scoring below this are filtered out
RELEVANCE_THRESHOLD = 20


class MatchingEngine:
    """Deterministic multi-factor scoring engine for matching demand agents to opportunities."""

    def __init__(self, threshold: int = RELEVANCE_THRESHOLD) -> None:
        self.threshold = threshold

    def score_agents(
        self,
        opportunity: OpportunityRecord,
        demand_agents: list[DemandAgentProfile],
    ) -> MatchResult:
        """Score all demand agents against an opportunity and return filtered results."""
        signal = opportunity.signal
        scored: list[MatchScore] = []
        matched_ids: list[str] = []

        for agent in demand_agents:
            sport_score = self._score_sport(signal.sport, agent)
            reach_score = self._score_reach(signal.audience.projected_reach, agent)
            budget_score = self._score_budget(signal.min_price, agent)
            format_score = self._score_format(signal.available_formats, agent)

            total = sport_score + reach_score + budget_score + format_score

            match_score = MatchScore(
                demand_agent_id=agent.agent_id,
                organization=agent.organization,
                relevance_score=total,
                sport_match=sport_score,
                reach_match=reach_score,
                budget_match=budget_score,
                format_match=format_score,
                reasoning=self._build_reasoning(
                    agent, sport_score, reach_score, budget_score, format_score, total,
                ),
            )
            scored.append(match_score)

            if total >= self.threshold:
                matched_ids.append(agent.agent_id)

        # Sort by relevance score descending
        scored.sort(key=lambda s: s.relevance_score, reverse=True)

        return MatchResult(
            opportunity_id=opportunity.opportunity_id,
            scored_agents=scored,
            matched_agent_ids=matched_ids,
        )

    # ------------------------------------------------------------------
    # Factor scoring (each returns 0-25)
    # ------------------------------------------------------------------

    @staticmethod
    def _score_sport(opportunity_sport: str, agent: DemandAgentProfile) -> float:
        """25 if exact sport match, 10 if queries but different sport, 0 if none."""
        queries = agent.standing_queries
        if not queries:
            return 0.0

        for q in queries:
            if q.sport is not None and q.sport == opportunity_sport:
                return 25.0

        # Has queries but none match the sport
        return 10.0

    @staticmethod
    def _score_reach(projected_reach: int, agent: DemandAgentProfile) -> float:
        """Reach match: scaled by how well the opportunity meets the agent's min_reach."""
        queries = agent.standing_queries
        if not queries:
            return 15.0

        # Use the first query that specifies min_reach, or default
        min_reach = 0
        for q in queries:
            if q.min_reach > 0:
                min_reach = q.min_reach
                break

        if min_reach == 0:
            return 15.0

        raw = 25.0 * projected_reach / max(min_reach, 1)
        return min(25.0, raw)

    @staticmethod
    def _score_budget(min_price: float, agent: DemandAgentProfile) -> float:
        """Budget match: 25 if agent can fully afford, proportional otherwise."""
        budget_max = agent.brand_profile.budget_per_deal_max
        if min_price <= 0:
            return 25.0
        return 25.0 * min(1.0, budget_max / max(min_price, 1))

    @staticmethod
    def _score_format(
        available_formats: list[str],
        agent: DemandAgentProfile,
    ) -> float:
        """Format match: 25 if overlap, 12 if no preference, 0 if no overlap."""
        queries = agent.standing_queries
        if not queries:
            return 12.0

        # Collect all desired formats across standing queries
        desired: set[str] = set()
        for q in queries:
            desired.update(q.content_formats)

        if not desired:
            return 12.0

        available_set = set(str(f) for f in available_formats)
        if desired & available_set:
            return 25.0

        return 0.0

    @staticmethod
    def _build_reasoning(
        agent: DemandAgentProfile,
        sport: float,
        reach: float,
        budget: float,
        fmt: float,
        total: float,
    ) -> str:
        parts = [
            f"sport={sport:.0f}",
            f"reach={reach:.0f}",
            f"budget={budget:.0f}",
            f"format={fmt:.0f}",
            f"total={total:.0f}",
        ]
        return f"{agent.organization}: {', '.join(parts)}"


# Singleton
matching_engine = MatchingEngine()
