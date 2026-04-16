"""AAX Demo — Phase 2: Multi-Agent Competition.

Orchestrates all 4 agents: Pixology (supply), Nike, Gatorade, Campus Pizza (demand).
Run with: cd agents && python run_demo.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base import AAXAgentClient
from pixology_supply.agent import PixologySupplyAgent
from nike_demand.agent import NikeDemandAgent
from gatorade_demand.agent import GatoradeDemandAgent
from local_biz_demand.agent import CampusPizzaDemandAgent


async def main():
    print("=" * 60)
    print("  AAX DEMO — Phase 2: Multi-Agent Competition")
    print("=" * 60)

    agents_dir = os.path.dirname(os.path.abspath(__file__))

    # ------------------------------------------------------------------
    # Step 1: Register all 4 agents
    # ------------------------------------------------------------------
    print("\n--- Step 1: Register Agents ---")

    pixology = PixologySupplyAgent(
        config_path=os.path.join(agents_dir, "pixology_supply", "config.yaml")
    )
    nike = NikeDemandAgent(
        config_path=os.path.join(agents_dir, "nike_demand", "config.yaml")
    )
    gatorade = GatoradeDemandAgent(
        config_path=os.path.join(agents_dir, "gatorade_demand", "config.yaml")
    )
    campus_pizza = CampusPizzaDemandAgent(
        config_path=os.path.join(agents_dir, "local_biz_demand", "config.yaml")
    )

    await pixology.start()
    await asyncio.sleep(0.5)
    await nike.start()
    await asyncio.sleep(0.5)
    await gatorade.start()
    await asyncio.sleep(0.5)
    await campus_pizza.start()
    await asyncio.sleep(0.5)

    print("   All 4 agents registered.")

    # ------------------------------------------------------------------
    # Step 2: Pixology signals a moment
    # ------------------------------------------------------------------
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
    matched = opp_result.get("matched_count", 0)
    print(f"   Opportunity: {opp_id}")
    print(f"   Deal: {deal_id}")
    print(f"   Matched demand agents: {matched}")

    # Show pre-screen results
    for r in opp_result.get("prescreen_results", []):
        status = "CLEARED" if r["status"] == "cleared" else "BLOCKED"
        print(f"   Pre-screen: {r['organization']} -> {status}")

    await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    # Step 3: All demand agents evaluate in parallel
    # ------------------------------------------------------------------
    print("\n--- Step 3: Demand Agents Evaluate ---")
    notification = {
        "opportunity_id": opp_id,
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
        "relevance_score": 0,
        "supply_agent": {"org": "Pixology", "reputation_score": "4.9"},
    }

    print("\n   [Nike]")
    nike_proposal = nike.evaluate_opportunity(notification)

    print("\n   [Gatorade]")
    gatorade_proposal = gatorade.evaluate_opportunity(notification)

    print("\n   [Campus Pizza]")
    campus_pizza_proposal = campus_pizza.evaluate_opportunity(notification)

    await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    # Step 4: Submit proposals (all that didn't pass)
    # ------------------------------------------------------------------
    print("\n--- Step 4: Submit Proposals ---")
    results = {}
    agent_proposals = [
        ("Nike", nike, nike_proposal),
        ("Gatorade", gatorade, gatorade_proposal),
        ("Campus Pizza", campus_pizza, campus_pizza_proposal),
    ]

    for name, agent, proposal in agent_proposals:
        if proposal:
            result = await agent.client.submit_proposal(opp_id, proposal)
            results[name] = result
            status = result.get("status", "unknown")
            conflict = result.get("conflict_status", "n/a")
            print(f"   {name}: {status} (conflict: {conflict})")
            if status == "conflict_blocked":
                conflicts = result.get("conflict_result", {}).get("conflicts", [])
                if conflicts:
                    print(f"      BLOCKED: {conflicts[0].get('description', 'unknown conflict')}")
        else:
            print(f"   {name}: PASSED (didn't bid)")

    await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    # Step 5: Find winning proposal (highest scored, non-blocked)
    # ------------------------------------------------------------------
    print("\n--- Step 5: Select Winner ---")
    winning_name = None
    winning_result = None
    for name in ["Nike", "Gatorade", "Campus Pizza"]:
        r = results.get(name)
        if r and r.get("status") == "submitted":
            if winning_result is None:
                winning_name = name
                winning_result = r

    if not winning_result:
        print("   No valid proposals! Demo cannot continue.")
        return

    print(f"   Winner: {winning_name}")

    # ------------------------------------------------------------------
    # Step 6: Supply evaluates winner's proposal
    # ------------------------------------------------------------------
    print("\n--- Step 6: Pixology Evaluates Winning Proposal ---")
    prop_id = winning_result["proposal_id"]

    # Get the winning agent's proposal data
    if winning_name == "Nike":
        winning_proposal = nike_proposal
    elif winning_name == "Gatorade":
        winning_proposal = gatorade_proposal
    else:
        winning_proposal = campus_pizza_proposal

    eval_result = pixology.evaluate_proposal(winning_proposal)
    print(f"   Pixology decision: {eval_result['decision'].upper()}")
    print(f"   Reasoning: {eval_result['reasoning']}")

    await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    # Step 7: Pixology responds to the proposal
    # ------------------------------------------------------------------
    print("\n--- Step 7: Pixology Responds ---")
    response = await pixology.client.respond_to_proposal(prop_id, eval_result)
    print(f"   Result: {response.get('status')}")

    if response.get("deal_id"):
        print(f"   Deal ID: {response['deal_id']}")

    # If counter, winning demand agent evaluates
    if response.get("status") == "countered":
        print("\n--- Counter-Offer Round ---")
        if winning_name == "Nike":
            counter_eval = nike.evaluate_counter(response)
        elif winning_name == "Gatorade":
            counter_eval = gatorade.evaluate_counter(response)
        else:
            counter_eval = campus_pizza.evaluate_counter(response)

        print(f"   {winning_name} decision: {counter_eval['decision'].upper()}")
        print(f"   Reasoning: {counter_eval['reasoning']}")

        # If the demand agent accepts the counter, respond
        if counter_eval["decision"] == "accept":
            counter_prop_id = response.get("proposal_id", prop_id)
            counter_response = await (
                nike if winning_name == "Nike"
                else gatorade if winning_name == "Gatorade"
                else campus_pizza
            ).client.respond_to_proposal(counter_prop_id, counter_eval)
            print(f"   Counter result: {counter_response.get('status')}")

    await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    # Step 8: Check final deal status
    # ------------------------------------------------------------------
    print("\n--- Step 8: Final Deal Status ---")
    deal = await pixology.client.get_deal(deal_id)
    print(f"   Final state: {deal['state']}")
    print(f"   Supply: {deal.get('supply_org', 'unknown')}")
    print(f"   Demand: {deal.get('demand_org', 'unknown')}")
    terms = deal.get("deal_terms", {})
    if terms:
        price = terms.get("price", {}).get("amount", 0)
        fmt = terms.get("content_format", "")
        print(f"   Price: ${price}")
        if fmt:
            print(f"   Format: {fmt}")

    print("\n" + "=" * 60)
    print("  DEMO COMPLETE — 4 agents, multi-agent competition!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nError: {e}")
        print(
            "Make sure the server is running: "
            "cd server && uv run uvicorn src.main:app --reload"
        )
