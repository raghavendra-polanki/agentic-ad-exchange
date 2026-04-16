"""Campus Pizza Demand Agent — hyper-local, budget-conscious, MIT-only."""

import asyncio
import os
import sys

import httpx

# Add parent to path for base import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base import AAXAgentClient


class CampusPizzaDemandAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.client = AAXAgentClient()
        self.config = AAXAgentClient.load_config(config_path)
        self.budget_remaining = self.config["brand_profile"]["budget"]["per_month_max"]
        self.deals_active: list = []

    async def start(self):
        """Register with the exchange."""
        print("  Campus Pizza Demand Agent starting...")

        bp = self.config["brand_profile"]
        creds = await self.client.register(
            {
                "agent_type": "demand",
                "name": self.config["agent"]["name"],
                "organization": self.config["agent"]["organization"],
                "description": self.config["agent"]["description"],
                "callback_url": "http://localhost:8084/webhook",
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
                        "min_reach": 5000,
                        "content_formats": ["social_post"],
                    },
                ],
            }
        )
        print(f"  Registered: {creds['agent_id']}")
        return creds

    def evaluate_opportunity(self, notification: dict) -> dict | None:
        """Evaluate an opportunity. HARD FILTER: MIT athletes only."""
        signal = notification.get("signal", {})
        subjects = signal.get("subjects", [])

        # HARD FILTER: Must be MIT
        if subjects:
            school = subjects[0].get("school", "")
            if school.upper() != "MIT":
                print(f"  PASS — school '{school}' is not MIT (hard filter)")
                return None
        else:
            print("  PASS — no subjects listed")
            return None

        reach = signal.get("audience", {}).get("projected_reach", 0)
        min_reach = self.config["strategy"]["min_reach"]

        if reach < min_reach:
            print(f"  PASS — reach {reach:,} below minimum {min_reach:,}")
            return None

        # Score the opportunity
        scores = self._score_opportunity(signal)

        if scores["overall"] < 30:
            print(
                f"  PASS — overall score {scores['overall']:.0f}/100 below threshold"
            )
            return None

        # Build proposal
        price = self._calculate_bid_price(signal, scores)

        proposal = {
            "opportunity_id": notification.get("opportunity_id", ""),
            "deal_terms": {
                "price": {"amount": price, "currency": "USD"},
                "content_format": "social_post",
                "platforms": ["instagram"],
                "usage_rights_duration_days": 3,
                "exclusivity_window_hours": 0,
                "brand_assets": {
                    "required_logos": ["campus_pizza_logo.png"],
                    "required_messaging": (
                        f"Fuel Your Game Day — {signal.get('content_description', '')}"
                    ),
                    "color_palette": ["#CC0000", "#FFD700", "#FFFFFF"],
                },
                "messaging_guidelines": (
                    "Casual, fun, community tone. Celebrate the local athlete."
                ),
                "compliance_disclosures": ["#ad", "#NIL"],
            },
            "reasoning": scores.get("reasoning", ""),
            "scores": scores,
        }

        print(f"  BID — ${price} | Score: {scores['overall']:.0f}/100")
        return proposal

    def evaluate_counter(self, counter: dict) -> dict:
        """Evaluate a counter-offer. ALWAYS reject if price > original bid."""
        counter_terms = counter.get("counter_terms", {})
        counter_price = counter_terms.get("price", {}).get("amount", 0)
        original_price = counter.get("original_price", counter_price)

        if counter_price > original_price:
            return {
                "decision": "reject",
                "reasoning": (
                    f"Counter price ${counter_price} exceeds our original bid "
                    f"${original_price}. Budget is firm. Rejecting."
                ),
            }

        return {
            "decision": "accept",
            "reasoning": (
                f"Counter price ${counter_price} is at or below our bid. Accepting."
            ),
        }

    def _score_opportunity(self, signal: dict) -> dict:
        """Simple 3-dimension scoring for budget-conscious local brand."""
        reach = signal.get("audience", {}).get("projected_reach", 0)
        min_price = signal.get("min_price", 0)
        subjects = signal.get("subjects", [])

        # School match (40%): 10 if MIT, 0 otherwise
        school = subjects[0].get("school", "") if subjects else ""
        school_match = 10.0 if school.upper() == "MIT" else 0.0

        # Audience fit (30%): reach / 20k * 10, capped at 10
        audience_fit = min(reach / 20000 * 10, 10)

        # Budget fit (30%): 8.0 if min_price <= 200, else 3.0
        budget_fit = 8.0 if min_price <= 200 else 3.0

        overall = (
            school_match * 0.40
            + audience_fit * 0.30
            + budget_fit * 0.30
        ) * 10

        reasoning = (
            f"{'MIT' if school_match == 10 else school} athlete, "
            f"{reach:,} projected reach. "
            f"Budget {'fits' if budget_fit >= 8 else 'tight'} at min ${min_price}. "
            f"Score: {overall:.0f}/100. "
            f"{'PROCEED WITH BID' if overall >= 30 else 'PASS'}."
        )

        return {
            "school_match": school_match,
            "audience_fit": audience_fit,
            "budget_fit": budget_fit,
            "overall": overall,
            "reasoning": reasoning,
        }

    def _calculate_bid_price(self, signal: dict, scores: dict) -> float:
        """Simple tiered pricing for small budget."""
        max_price = self.config["brand_profile"]["budget"]["per_deal_max"]

        if scores["overall"] > 50:
            price = 200
        elif scores["overall"] > 30:
            price = 150
        else:
            price = 100

        return min(price, max_price)


async def main():
    """Run the Campus Pizza agent in demo mode."""
    agent = CampusPizzaDemandAgent()

    try:
        await agent.start()
        print("Campus Pizza agent ready. Waiting for opportunities...")

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
            "relevance_score": 60.0,
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
