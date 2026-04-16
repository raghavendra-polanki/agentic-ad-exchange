"""Tests for the Matching Engine — deterministic relevance scoring."""

from src.matching.scorer import MatchingEngine
from src.schemas.agents import BrandProfile, DemandAgentProfile, StandingQuery
from src.schemas.common import ContentFormat, Sport
from src.schemas.matching import MatchResult
from src.schemas.opportunities import AudienceInfo, OpportunityRecord, OpportunitySignal, SubjectInfo


def _make_opportunity(
    sport: Sport = Sport.BASKETBALL,
    projected_reach: int = 50000,
    min_price: float = 500.0,
    available_formats: list[ContentFormat] | None = None,
) -> OpportunityRecord:
    """Helper: build a minimal OpportunityRecord for testing."""
    if available_formats is None:
        available_formats = [ContentFormat.GAMEDAY_GRAPHIC]
    return OpportunityRecord(
        opportunity_id="opp-test-001",
        supply_agent_id="pixology-001",
        supply_org="Pixology",
        signal=OpportunitySignal(
            content_description="Test moment",
            subjects=[SubjectInfo(athlete_name="Jane Doe", school="MIT", sport=sport)],
            audience=AudienceInfo(projected_reach=projected_reach),
            available_formats=available_formats,
            min_price=min_price,
            sport=sport,
        ),
    )


def _make_agent(
    agent_id: str = "nike-001",
    organization: str = "Nike",
    standing_queries: list[StandingQuery] | None = None,
    budget_per_deal_max: float = 5000.0,
) -> DemandAgentProfile:
    """Helper: build a minimal DemandAgentProfile for testing."""
    return DemandAgentProfile(
        agent_id=agent_id,
        name=f"{organization} Agent",
        organization=organization,
        brand_profile=BrandProfile(budget_per_deal_max=budget_per_deal_max),
        standing_queries=standing_queries or [],
    )


class TestSportMatch:
    def test_matching_sport_match_exact(self):
        """Agent with basketball query vs basketball opportunity -> sport_match=25."""
        engine = MatchingEngine()
        opp = _make_opportunity(sport=Sport.BASKETBALL)
        agent = _make_agent(
            standing_queries=[StandingQuery(sport=Sport.BASKETBALL)]
        )

        result = engine.score_agents(opp, [agent])

        assert len(result.scored_agents) == 1
        assert result.scored_agents[0].sport_match == 25.0

    def test_matching_sport_no_queries(self):
        """Agent with no standing queries -> sport_match=0."""
        engine = MatchingEngine()
        opp = _make_opportunity(sport=Sport.BASKETBALL)
        agent = _make_agent(standing_queries=[])

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].sport_match == 0.0

    def test_matching_sport_different_sport(self):
        """Agent with football query vs basketball opportunity -> sport_match=10."""
        engine = MatchingEngine()
        opp = _make_opportunity(sport=Sport.BASKETBALL)
        agent = _make_agent(
            standing_queries=[StandingQuery(sport=Sport.FOOTBALL)]
        )

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].sport_match == 10.0


class TestReachMatch:
    def test_matching_reach_scaling(self):
        """Agent with 50k min_reach vs 150k reach opportunity -> reach_match=25 (capped)."""
        engine = MatchingEngine()
        opp = _make_opportunity(projected_reach=150000)
        agent = _make_agent(
            standing_queries=[StandingQuery(sport=Sport.BASKETBALL, min_reach=50000)]
        )

        result = engine.score_agents(opp, [agent])

        # 25 * 150000 / 50000 = 75.0, capped at 25
        assert result.scored_agents[0].reach_match == 25.0

    def test_matching_reach_partial(self):
        """Agent with 100k min_reach vs 50k reach -> reach_match=12.5."""
        engine = MatchingEngine()
        opp = _make_opportunity(projected_reach=50000)
        agent = _make_agent(
            standing_queries=[StandingQuery(sport=Sport.BASKETBALL, min_reach=100000)]
        )

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].reach_match == 12.5

    def test_matching_reach_no_min(self):
        """Agent with no min_reach in queries -> reach_match=15."""
        engine = MatchingEngine()
        opp = _make_opportunity(projected_reach=50000)
        agent = _make_agent(
            standing_queries=[StandingQuery(sport=Sport.BASKETBALL, min_reach=0)]
        )

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].reach_match == 15.0


class TestBudgetMatch:
    def test_matching_budget_adequate(self):
        """Agent with $5000 budget vs $500 min_price -> budget_match=25."""
        engine = MatchingEngine()
        opp = _make_opportunity(min_price=500.0)
        agent = _make_agent(budget_per_deal_max=5000.0)

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].budget_match == 25.0

    def test_matching_budget_insufficient(self):
        """Agent with $200 budget vs $500 min_price -> budget_match=10."""
        engine = MatchingEngine()
        opp = _make_opportunity(min_price=500.0)
        agent = _make_agent(budget_per_deal_max=200.0)

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].budget_match == 10.0

    def test_matching_budget_exact(self):
        """Agent with $500 budget vs $500 min_price -> budget_match=25."""
        engine = MatchingEngine()
        opp = _make_opportunity(min_price=500.0)
        agent = _make_agent(budget_per_deal_max=500.0)

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].budget_match == 25.0


class TestFormatMatch:
    def test_matching_format_overlap(self):
        """Signal has gameday_graphic, agent wants gameday_graphic -> format_match=25."""
        engine = MatchingEngine()
        opp = _make_opportunity(available_formats=[ContentFormat.GAMEDAY_GRAPHIC])
        agent = _make_agent(
            standing_queries=[
                StandingQuery(
                    sport=Sport.BASKETBALL,
                    content_formats=[ContentFormat.GAMEDAY_GRAPHIC],
                )
            ]
        )

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].format_match == 25.0

    def test_matching_format_no_overlap(self):
        """Signal has gameday_graphic, agent wants video_clip -> format_match=0."""
        engine = MatchingEngine()
        opp = _make_opportunity(available_formats=[ContentFormat.GAMEDAY_GRAPHIC])
        agent = _make_agent(
            standing_queries=[
                StandingQuery(
                    sport=Sport.BASKETBALL,
                    content_formats=[ContentFormat.VIDEO_CLIP],
                )
            ]
        )

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].format_match == 0.0

    def test_matching_format_no_preference(self):
        """Agent has queries but no format preference -> format_match=12."""
        engine = MatchingEngine()
        opp = _make_opportunity(available_formats=[ContentFormat.GAMEDAY_GRAPHIC])
        agent = _make_agent(
            standing_queries=[StandingQuery(sport=Sport.BASKETBALL)]
        )

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].format_match == 12.0


class TestThresholdFilter:
    def test_matching_threshold_filter(self):
        """Agent scoring below 20 should not be in matched_agent_ids."""
        engine = MatchingEngine(threshold=20)
        opp = _make_opportunity(
            sport=Sport.BASKETBALL,
            min_price=500.0,
            available_formats=[ContentFormat.GAMEDAY_GRAPHIC],
        )
        # Agent with no queries -> sport=0, reach=15(default), format=12(default)
        # Budget: 200/500 * 25 = 10
        # Total = 0 + 15 + 10 + 12 = 37 -- wait, that's > 20.
        # Need a truly low-scoring agent. No queries + bad budget + specific format mismatch.
        # Actually with no queries: sport=0, reach=15, budget=10, format=12 = 37.
        # Let me use an agent with queries but all mismatches.
        low_agent = _make_agent(
            agent_id="low-agent",
            organization="LowBudget",
            budget_per_deal_max=20.0,  # 20/500 * 25 = 1
            standing_queries=[
                StandingQuery(
                    sport=Sport.SWIMMING,  # mismatch -> 10
                    min_reach=500000,  # 50000/500000 * 25 = 2.5
                    content_formats=[ContentFormat.VIDEO_CLIP],  # mismatch -> 0
                )
            ],
        )
        # Total = 10 + 2.5 + 1 + 0 = 13.5 -> below 20

        result = engine.score_agents(opp, [low_agent])

        assert result.scored_agents[0].relevance_score < 20
        assert "low-agent" not in result.matched_agent_ids

    def test_matching_threshold_pass(self):
        """Agent scoring >= 20 should be in matched_agent_ids."""
        engine = MatchingEngine(threshold=20)
        opp = _make_opportunity(sport=Sport.BASKETBALL)
        agent = _make_agent(
            standing_queries=[
                StandingQuery(
                    sport=Sport.BASKETBALL,
                    content_formats=[ContentFormat.GAMEDAY_GRAPHIC],
                )
            ],
            budget_per_deal_max=5000.0,
        )

        result = engine.score_agents(opp, [agent])

        assert result.scored_agents[0].relevance_score >= 20
        assert "nike-001" in result.matched_agent_ids


class TestMultiAgent:
    def test_matching_sorted_by_score(self):
        """Multiple agents should be sorted by relevance_score descending."""
        engine = MatchingEngine()
        opp = _make_opportunity(sport=Sport.BASKETBALL)

        high_agent = _make_agent(
            agent_id="high-001",
            organization="HighBrand",
            standing_queries=[
                StandingQuery(
                    sport=Sport.BASKETBALL,
                    content_formats=[ContentFormat.GAMEDAY_GRAPHIC],
                )
            ],
            budget_per_deal_max=10000.0,
        )
        low_agent = _make_agent(
            agent_id="low-001",
            organization="LowBrand",
            standing_queries=[],
            budget_per_deal_max=100.0,
        )

        result = engine.score_agents(opp, [low_agent, high_agent])

        assert result.scored_agents[0].demand_agent_id == "high-001"
        assert result.scored_agents[1].demand_agent_id == "low-001"

    def test_matching_result_type(self):
        """score_agents should return a MatchResult."""
        engine = MatchingEngine()
        opp = _make_opportunity()
        agent = _make_agent()

        result = engine.score_agents(opp, [agent])

        assert isinstance(result, MatchResult)
        assert result.opportunity_id == "opp-test-001"
