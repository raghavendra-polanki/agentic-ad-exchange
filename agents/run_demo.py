"""AAX Demo — Run the full deal flow: register agents, signal opportunity, negotiate, close."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base import AAXAgentClient
from pixology_supply.agent import PixologySupplyAgent
from nike_demand.agent import NikeDemandAgent


async def main():
    print("=" * 60)
    print("  AAX DEMO — Autonomous Deal Flow")
    print("=" * 60)

    # 1. Register both agents FIRST
    print("\n--- Step 1: Register Agents ---")
    pixology = PixologySupplyAgent(
        config_path=os.path.join(os.path.dirname(__file__), "pixology_supply", "config.yaml")
    )
    nike = NikeDemandAgent(
        config_path=os.path.join(os.path.dirname(__file__), "nike_demand", "config.yaml")
    )

    await pixology.start()
    await nike.start()

    # 2. Pixology signals the moment
    print("\n--- Step 2: Signal Opportunity ---")
    opp_result = await pixology.signal_moment(
        description="Jane Doe scores 1000th career point",
        athlete="Jane Doe",
        school="MIT",
        sport="basketball",
        reach=150000,
    )

    opp_id = opp_result["opportunity_id"]
    deal_id = opp_result["deal_id"]
    matched = opp_result["matched_count"]
    print(f"   Opportunity: {opp_id}")
    print(f"   Deal: {deal_id}")
    print(f"   Matched demand agents: {matched}")

    # Show pre-screen results
    for r in opp_result.get("prescreen_results", []):
        status = "CLEARED" if r["status"] == "cleared" else "BLOCKED"
        print(f"   Pre-screen: {r['organization']} → {status}")

    # 3. Nike evaluates and bids
    print("\n--- Step 3: Nike Evaluates & Bids ---")
    notification = {
        "opportunity_id": opp_id,
        "signal": {
            "content_description": "Jane Doe scores 1000th career point",
            "subjects": [{"athlete_name": "Jane Doe", "school": "MIT", "sport": "basketball"}],
            "audience": {"projected_reach": 150000, "demographics": "18-24, sports fans", "trending_score": 85.0},
            "available_formats": ["gameday_graphic", "social_post"],
            "min_price": 500,
        },
        "relevance_score": 82.0,
        "supply_agent": {"org": "Pixology", "reputation_score": "4.9"},
    }

    proposal = nike.evaluate_opportunity(notification)
    if not proposal:
        print("   Nike passed on opportunity")
        return

    # Submit proposal
    prop_result = await nike.client.submit_proposal(opp_id, proposal)
    print(f"   Proposal: {prop_result.get('proposal_id')}")
    print(f"   Conflict status: {prop_result.get('conflict_status')}")

    if prop_result.get("status") == "conflict_blocked":
        print(f"   BLOCKED: {prop_result['conflict_result']['conflicts'][0]['description']}")
        return

    prop_id = prop_result["proposal_id"]

    # 4. Pixology evaluates Nike's proposal
    print("\n--- Step 4: Pixology Evaluates Proposal ---")
    eval_result = pixology.evaluate_proposal(proposal)
    print(f"   Decision: {eval_result['decision'].upper()}")
    print(f"   Reasoning: {eval_result['reasoning']}")

    # 5. Pixology responds
    print("\n--- Step 5: Pixology Responds ---")
    response = await pixology.client.respond_to_proposal(prop_id, eval_result)
    print(f"   Result: {response.get('status')}")

    if response.get("deal_id"):
        print(f"   Deal ID: {response['deal_id']}")

    # 6. Check final deal status
    print("\n--- Step 6: Deal Status ---")
    deal = await pixology.client.get_deal(deal_id)
    print(f"   State: {deal['state']}")
    print(f"   Supply: {deal['supply_org']}")
    print(f"   Demand: {deal['demand_org']}")
    terms = deal.get("deal_terms", {})
    if terms:
        price = terms.get("price", {}).get("amount", 0)
        fmt = terms.get("content_format", "")
        print(f"   Price: ${price}")
        print(f"   Format: {fmt}")

    print("\n" + "=" * 60)
    print("  DEMO COMPLETE — Full autonomous deal flow!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the server is running: cd server && uv run uvicorn src.main:app --reload")
