"""Nike Demand Agent — premium athletic brand, aggressive bidder."""

import asyncio
import os
import sys

import httpx

# Add parent to path for base import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base import AAXAgentClient


class NikeDemandAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.client = AAXAgentClient()
        self.config = AAXAgentClient.load_config(config_path)
        self.budget_remaining = self.config["brand_profile"]["budget"]["per_month_max"]
        self.deals_active: list = []

        # LLM config (optional — falls back to rule-based)
        self.llm_enabled = bool(
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )

    async def start(self):
        """Register with the exchange."""
        print("✓ Nike Demand Agent starting...")

        bp = self.config["brand_profile"]
        creds = await self.client.register(
            {
                "agent_type": "demand",
                "name": self.config["agent"]["name"],
                "organization": self.config["agent"]["organization"],
                "description": self.config["agent"]["description"],
                "callback_url": "http://localhost:8082/webhook",
                "brand_profile": {
                    "tone": bp["tone"],
                    "tagline": bp["tagline"],
                    "budget_per_deal_max": bp["budget"]["per_deal_max"],
                    "budget_per_month_max": bp["budget"]["per_month_max"],
                    "competitor_exclusions": bp["exclusions"]["competitors"],
                    "auto_approve_below": bp["approval_rules"]["auto_approve_below"],
                },
                "standing_queries": [
                    {"sport": "basketball", "min_reach": 50000},
                    {"sport": "football", "min_reach": 100000},
                ],
            }
        )
        print(f"✅ Registered: {creds['agent_id']}")
        return creds

    def evaluate_opportunity(self, notification: dict) -> dict | None:
        """Evaluate an opportunity and decide whether to bid."""
        signal = notification.get("signal", {})
        reach = signal.get("audience", {}).get("projected_reach", 0)
        min_reach = self.config["strategy"]["min_reach"]

        if reach < min_reach:
            print(f"  ⏭ PASS — reach {reach:,} below minimum {min_reach:,}")
            return None

        # Score the opportunity
        scores = self._score_opportunity(signal)

        if scores["overall"] < 50:
            print(
                f"  ⏭ PASS — overall score {scores['overall']:.0f}/100 below threshold"
            )
            return None

        # Build proposal
        price = self._calculate_bid_price(signal, scores)
        preferred_format = self.config["strategy"]["preferred_formats"][0]

        proposal = {
            "opportunity_id": notification.get("opportunity_id", ""),
            "deal_terms": {
                "price": {"amount": price, "currency": "USD"},
                "content_format": preferred_format,
                "platforms": ["instagram", "twitter"],
                "usage_rights_duration_days": 7,
                "exclusivity_window_hours": 24,
                "brand_assets": {
                    "required_logos": ["nike_swoosh_white.png"],
                    "required_messaging": (
                        f"Just Do It — {signal.get('content_description', '')}"
                    ),
                    "color_palette": ["#000000", "#FFFFFF"],
                },
                "messaging_guidelines": (
                    "Empowering, aspirational tone. Focus on the achievement."
                ),
                "compliance_disclosures": ["#ad", "#NIL"],
            },
            "reasoning": scores.get("reasoning", ""),
            "scores": scores,
        }

        print(f"  💰 BID — ${price} | Score: {scores['overall']:.0f}/100")
        return proposal

    def evaluate_counter(self, counter: dict) -> dict:
        """Evaluate a counter-offer from supply agent."""
        counter_terms = counter.get("counter_terms", {})
        round_num = counter.get("round", 1)
        max_rounds = counter.get("max_rounds", 3)

        price = counter_terms.get("price", {}).get("amount", 0)
        max_price = self.config["brand_profile"]["budget"]["per_deal_max"]

        if price > max_price:
            return {
                "decision": "reject",
                "reasoning": f"Price ${price} exceeds max ${max_price}",
            }

        # Nike is aggressive — tend to accept counters if price is reasonable
        if price <= max_price * 0.8 or round_num >= max_rounds:
            return {
                "decision": "accept",
                "reasoning": (
                    f"Counter terms acceptable. Price ${price} within budget. Accepting."
                ),
            }

        # Counter back slightly
        return {
            "decision": "counter",
            "counter_terms": {
                **counter_terms,
                "price": {"amount": price * 0.9, "currency": "USD"},
            },
            "reasoning": f"Countering at ${price * 0.9:.0f} (10% reduction).",
        }

    def _score_opportunity(self, signal: dict) -> dict:
        """Score an opportunity across multiple dimensions."""
        reach = signal.get("audience", {}).get("projected_reach", 0)
        _trending = signal.get("audience", {}).get("trending_score", 0)

        audience_fit = min(reach / 200000 * 10, 10)
        description = signal.get("content_description", "").lower()
        brand_narrative = (
            8.0
            if "milestone" in description or "record" in description
            else 6.0
        )
        projected_roi = min((reach / 100000) * 7, 10)
        competitive_pos = 8.0  # Nike is the premium — always strong

        overall = (
            audience_fit * 0.3
            + brand_narrative * 0.25
            + projected_roi * 0.25
            + competitive_pos * 0.2
        ) * 10

        reasoning = (
            f"D1 sports content, {reach:,} projected reach. "
            f"{'Strong' if brand_narrative >= 8 else 'Moderate'} narrative angle "
            f"for Just Do It campaign. "
            f"Score: {overall:.0f}/100. "
            f"{'PROCEED WITH BID' if overall >= 50 else 'PASS'}."
        )

        return {
            "audience_fit": audience_fit,
            "brand_alignment": brand_narrative,
            "projected_roi": projected_roi,
            "price_adequacy": 0,  # Set after pricing
            "content_feasibility": 8.0,
            "timeline_fit": 8.0,
            "overall": overall,
            "reasoning": reasoning,
        }

    def _calculate_bid_price(self, signal: dict, scores: dict) -> float:
        """Calculate bid price based on opportunity quality."""
        base_price = 500
        reach = signal.get("audience", {}).get("projected_reach", 0)

        # Scale by reach
        reach_multiplier = min(reach / 100000, 3.0)

        # Scale by quality
        quality_multiplier = scores["overall"] / 70  # 70 is "good"

        price = base_price * reach_multiplier * quality_multiplier
        max_price = self.config["brand_profile"]["budget"]["per_deal_max"]

        return min(round(price / 50) * 50, max_price)  # Round to nearest $50


async def main():
    """Run the Nike agent in demo mode."""
    agent = NikeDemandAgent()

    try:
        await agent.start()
        print("👟 Nike agent ready. Waiting for opportunities...")

        # Simulate receiving an opportunity notification
        demo_notification = {
            "opportunity_id": "opp_demo_001",
            "signal": {
                "content_description": "Jane Doe scores 1000th career point",
                "subjects": [
                    {
                        "athlete_name": "Jane Doe",
                        "school": "MIT",
                        "sport": "basketball",
                    }
                ],
                "audience": {
                    "projected_reach": 150000,
                    "demographics": "18-24, sports fans",
                    "trending_score": 85.0,
                },
                "available_formats": ["gameday_graphic", "social_post"],
                "min_price": 500,
            },
            "relevance_score": 82.0,
            "supply_agent": {"org": "Pixology", "reputation_score": "4.9"},
        }

        print(
            f"\n📨 Received opportunity: "
            f"{demo_notification['signal']['content_description']}"
        )
        proposal = agent.evaluate_opportunity(demo_notification)

        if proposal:
            result = await agent.client.submit_proposal(
                demo_notification["opportunity_id"], proposal
            )
            print(f"📊 Proposal result: {result}")

    except httpx.ConnectError:
        print("⚠️  Cannot connect to AAX exchange at localhost:8080.")
        print(
            "   Start the server first: "
            "cd server && uv run uvicorn src.main:app --reload"
        )
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
