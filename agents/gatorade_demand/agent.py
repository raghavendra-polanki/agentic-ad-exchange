"""Gatorade Demand Agent — selective bidder, performance-focused hydration brand."""

import asyncio
import os
import sys

import httpx

# Add parent to path for base import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base import AAXAgentClient


class GatoradeDemandAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.client = AAXAgentClient()
        self.config = AAXAgentClient.load_config(config_path)
        self.budget_remaining = self.config["brand_profile"]["budget"]["per_month_max"]
        self.deals_active: list = []

    async def start(self):
        """Register with the exchange."""
        print("  Gatorade Demand Agent starting...")

        bp = self.config["brand_profile"]
        creds = await self.client.register(
            {
                "agent_type": "demand",
                "name": self.config["agent"]["name"],
                "organization": self.config["agent"]["organization"],
                "description": self.config["agent"]["description"],
                "callback_url": "http://localhost:8083/webhook",
                "brand_profile": {
                    "tone": bp["tone"],
                    "tagline": bp["tagline"],
                    "budget_per_deal_max": bp["budget"]["per_deal_max"],
                    "budget_per_month_max": bp["budget"]["per_month_max"],
                    "competitor_exclusions": bp["exclusions"]["competitors"],
                    "auto_approve_below": bp["approval_rules"]["auto_approve_below"],
                },
                "standing_queries": [
                    {
                        "sport": "basketball",
                        "min_reach": 30000,
                        "content_formats": ["social_post", "gameday_graphic"],
                    },
                ],
            }
        )
        print(f"  Registered: {creds['agent_id']}")
        return creds

    def evaluate_opportunity(self, notification: dict) -> dict | None:
        """Evaluate an opportunity and decide whether to bid."""
        signal = notification.get("signal", {})
        reach = signal.get("audience", {}).get("projected_reach", 0)
        min_reach = self.config["strategy"]["min_reach"]

        if reach < min_reach:
            print(f"  PASS — reach {reach:,} below minimum {min_reach:,}")
            return None

        # Score the opportunity
        scores = self._score_opportunity(signal)

        if scores["overall"] < 45:
            print(
                f"  PASS — overall score {scores['overall']:.0f}/100 below threshold"
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
                "exclusivity_window_hours": 12,
                "brand_assets": {
                    "required_logos": ["gatorade_bolt.png"],
                    "required_messaging": (
                        f"Is It In You? — {signal.get('content_description', '')}"
                    ),
                    "color_palette": ["#F47920", "#000000", "#FFFFFF"],
                },
                "messaging_guidelines": (
                    "Energetic, performance-focused tone. Tie into the athlete's effort."
                ),
                "compliance_disclosures": ["#ad", "#NIL"],
            },
            "reasoning": scores.get("reasoning", ""),
            "scores": scores,
        }

        print(f"  BID — ${price} | Score: {scores['overall']:.0f}/100")
        return proposal

    def evaluate_counter(self, counter: dict) -> dict:
        """Evaluate a counter-offer from supply agent."""
        counter_terms = counter.get("counter_terms", {})
        price = counter_terms.get("price", {}).get("amount", 0)
        max_price = self.config["brand_profile"]["budget"]["per_deal_max"]

        if price > max_price:
            return {
                "decision": "reject",
                "reasoning": f"Price ${price} exceeds budget max ${max_price}. Rejecting.",
            }

        return {
            "decision": "accept",
            "reasoning": (
                f"Counter price ${price} within budget (max ${max_price}). Accepting."
            ),
        }

    def _score_opportunity(self, signal: dict) -> dict:
        """Score an opportunity across 4 dimensions."""
        reach = signal.get("audience", {}).get("projected_reach", 0)
        description = signal.get("content_description", "").lower()

        # Audience fit (20%): reach / 50k * 10, capped at 10
        audience_fit = min(reach / 50000 * 10, 10)

        # Brand narrative (35%): performance keywords boost score
        performance_keywords = [
            "performance", "endurance", "record", "comeback", "overtime", "clutch",
        ]
        brand_narrative = (
            8.0
            if any(kw in description for kw in performance_keywords)
            else 5.5
        )

        # Projected ROI (25%): reach * (base bid) / 100k, normalized
        base_bid = 300
        raw_roi = (reach * base_bid) / 100000
        projected_roi = min(raw_roi / 500 * 10, 10)  # Normalize to 0-10

        # Competitive position (20%): default 7.0
        competitive_pos = 7.0

        overall = (
            audience_fit * 0.20
            + brand_narrative * 0.35
            + projected_roi * 0.25
            + competitive_pos * 0.20
        ) * 10

        reasoning = (
            f"Sports content, {reach:,} projected reach. "
            f"{'Strong' if brand_narrative >= 8 else 'Moderate'} performance narrative. "
            f"Score: {overall:.0f}/100. "
            f"{'PROCEED WITH BID' if overall >= 45 else 'PASS'}."
        )

        return {
            "audience_fit": audience_fit,
            "brand_narrative": brand_narrative,
            "projected_roi": projected_roi,
            "competitive_pos": competitive_pos,
            "overall": overall,
            "reasoning": reasoning,
        }

    def _calculate_bid_price(self, signal: dict, scores: dict) -> float:
        """Calculate bid price based on opportunity quality."""
        base_price = 300
        reach = signal.get("audience", {}).get("projected_reach", 0)

        # Scale by reach (capped at 2x)
        reach_multiplier = min(reach / 100000, 2.0)

        # Scale by quality
        quality_multiplier = scores["overall"] / 60

        price = base_price * reach_multiplier * quality_multiplier
        max_price = self.config["brand_profile"]["budget"]["per_deal_max"]

        # Round to nearest $25
        return min(round(price / 25) * 25, max_price)


async def main():
    """Run the Gatorade agent in demo mode."""
    agent = GatoradeDemandAgent()

    try:
        await agent.start()
        print("Gatorade agent ready. Waiting for opportunities...")

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
            "relevance_score": 75.0,
            "supply_agent": {"org": "Pixology", "reputation_score": "4.9"},
        }

        print(
            f"\nReceived opportunity: "
            f"{demo_notification['signal']['content_description']}"
        )
        proposal = agent.evaluate_opportunity(demo_notification)

        if proposal:
            result = await agent.client.submit_proposal(
                demo_notification["opportunity_id"], proposal
            )
            print(f"Proposal result: {result}")

    except httpx.ConnectError:
        print("Cannot connect to AAX exchange at localhost:8080.")
        print(
            "   Start the server first: "
            "cd server && uv run uvicorn src.main:app --reload"
        )
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
