"""Pixology Supply Agent — content creator for college athletics."""

import asyncio
import os
import sys

import httpx

# Add parent to path for base import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base import AAXAgentClient


class PixologySupplyAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.client = AAXAgentClient()
        self.config = AAXAgentClient.load_config(config_path)
        self.active_deals: dict = {}
        self.min_price = 500.0  # Minimum acceptable price

    async def start(self):
        """Register and begin operating."""
        print("🏀 Pixology Supply Agent starting...")

        # Register with exchange
        creds = await self.client.register(
            {
                "agent_type": "supply",
                "name": self.config["agent"]["name"],
                "organization": self.config["agent"]["organization"],
                "description": self.config["agent"]["description"],
                "callback_url": "http://localhost:8081/webhook",
                "supply_capabilities": {
                    "content_formats": self.config["capabilities"]["content_types"],
                    "sports": self.config["capabilities"]["sports"],
                    "turnaround_minutes": 5,
                    "max_concurrent_deals": self.config["capabilities"][
                        "max_concurrent_deals"
                    ],
                },
            }
        )
        print(f"✅ Registered: {creds['agent_id']}")
        return creds

    async def signal_moment(
        self,
        description: str,
        athlete: str,
        school: str,
        sport: str = "basketball",
        reach: int = 150000,
    ):
        """Signal a new monetizable moment to the exchange."""
        signal = {
            "content_description": description,
            "subjects": [
                {"athlete_name": athlete, "school": school, "sport": sport}
            ],
            "audience": {
                "projected_reach": reach,
                "demographics": "18-24, sports fans",
                "trending_score": 85.0,
            },
            "available_formats": ["gameday_graphic", "social_post"],
            "min_price": self.min_price,
            "sport": sport,
        }
        result = await self.client.signal_opportunity(signal)
        print(f"📡 Opportunity signaled: {description}")
        return result

    def evaluate_proposal(self, proposal: dict) -> dict:
        """Evaluate a proposal from a demand agent. Returns accept/counter/reject."""
        terms = proposal.get("deal_terms", {})
        price = terms.get("price", {}).get("amount", 0)

        # Scoring logic
        scores = {
            "price_adequacy": min(price / self.min_price * 10, 10),
            "brand_alignment": 9.0,  # Nike/premium brands score high
            "content_feasibility": 9.0,  # We can make anything
            "timeline_fit": 8.0,
            "overall": 0.0,
            "reasoning": "",
        }
        scores["overall"] = (
            scores["price_adequacy"] * 0.35
            + scores["brand_alignment"] * 0.25
            + scores["content_feasibility"] * 0.25
            + scores["timeline_fit"] * 0.15
        ) * 10  # Scale to 100

        if price < self.min_price:
            scores["reasoning"] = (
                f"Price ${price} below minimum ${self.min_price}. REJECT."
            )
            return {
                "decision": "reject",
                "scores": scores,
                "reasoning": scores["reasoning"],
            }

        if price < self.min_price * 1.2:
            # Counter for more
            scores["reasoning"] = (
                f"Price ${price} is acceptable but low. "
                "Countering for longer usage rights."
            )
            counter_terms = {
                **terms,
                "usage_rights_duration_days": 14,
                "exclusivity_window_hours": 48,
            }
            return {
                "decision": "counter",
                "counter_terms": counter_terms,
                "scores": scores,
                "reasoning": scores["reasoning"],
            }

        scores["reasoning"] = (
            f"Price ${price} above minimum. Brand is premium. ACCEPT."
        )
        return {
            "decision": "accept",
            "scores": scores,
            "reasoning": scores["reasoning"],
        }

    async def generate_content(self, brief: dict) -> dict:
        """Generate content based on creative brief. (Mock for Phase 1)"""
        print(
            f"🎨 Generating content for deal {brief.get('deal_id', 'unknown')}..."
        )
        # In production, this calls the real Pixology API
        return {
            "deal_id": brief.get("deal_id", ""),
            "content_url": "https://pixology.ai/content/mock-gameday-graphic.png",
            "format": brief.get("deal_terms", {}).get(
                "content_format", "gameday_graphic"
            ),
            "metadata": {
                "athlete": brief.get("athlete_name", ""),
                "school": brief.get("school", ""),
                "brand": brief.get("brand_name", ""),
                "generated_by": "pixology-agent-v1",
            },
        }


async def main():
    """Run the Pixology agent in demo mode."""
    agent = PixologySupplyAgent()

    try:
        # Register
        await agent.start()

        # Signal a demo moment
        result = await agent.signal_moment(
            description="Jane Doe scores 1000th career point",
            athlete="Jane Doe",
            school="MIT",
            sport="basketball",
            reach=150000,
        )
        print(f"📊 Opportunity result: {result}")

    except httpx.ConnectError:
        print("⚠️  Cannot connect to AAX exchange at localhost:8080.")
        print(
            "   Start the server first: cd server && uv run uvicorn src.main:app --reload"
        )
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
