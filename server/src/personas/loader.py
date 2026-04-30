"""Parse persona files (YAML frontmatter + markdown body) and seed the store."""

import logging
import re
from pathlib import Path

import yaml

from src.schemas.personas import BrandRules, ContentRules, TargetDemographics

logger = logging.getLogger("aax.personas")

# personas/ directory at repo root, alongside agents/
PERSONAS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "personas"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_persona_file(path: Path) -> tuple[dict, str]:
    """Split a markdown file into (frontmatter dict, body string).

    Raises ValueError if the file lacks frontmatter delimiters.
    """
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path} has no YAML frontmatter (expected '---' delimiters)")
    fm = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()
    return fm, body


def _build_brand_rules(agent_id: str, fm: dict, body: str) -> BrandRules:
    demos = fm.get("target_demographics") or {}
    return BrandRules(
        agent_id=agent_id,
        brand=fm.get("brand", "Unknown Brand"),
        agent_name=fm.get("agent_name", fm.get("brand", agent_id)),
        budget_per_deal_max=int(fm.get("budget_per_deal_max", 1000)),
        budget_per_month_max=int(fm.get("budget_per_month_max", 10000)),
        auto_approve_threshold_usd=int(fm.get("auto_approve_threshold_usd", 1000)),
        competitor_exclusions=list(fm.get("competitor_exclusions") or []),
        target_demographics=TargetDemographics(
            age_range=demos.get("age_range"),
            interests=list(demos.get("interests") or []),
        ),
        voice_md=body,
    )


def _build_content_rules(agent_id: str, fm: dict, body: str) -> ContentRules:
    return ContentRules(
        agent_id=agent_id,
        service=fm.get("service", "Content Service"),
        agent_name=fm.get("agent_name", fm.get("service", agent_id)),
        min_price_per_deal=int(fm.get("min_price_per_deal", 100)),
        max_concurrent_deals=int(fm.get("max_concurrent_deals", 5)),
        blocked_categories=list(fm.get("blocked_categories") or []),
        voice_md=body,
    )


def load_personas() -> tuple[dict[str, BrandRules], dict[str, ContentRules], list[dict]]:
    """Scan PERSONAS_DIR and return parsed BrandRules + ContentRules.

    Returns (brand_rules_by_agent_id, content_rules_by_agent_id, agent_seeds).
    `agent_seeds` is a list of dicts the bootstrap loop in main.py consumes
    to register managed agents with stable IDs.
    """
    brand_rules: dict[str, BrandRules] = {}
    content_rules: dict[str, ContentRules] = {}
    agent_seeds: list[dict] = []

    if not PERSONAS_DIR.exists():
        logger.warning("PERSONAS_DIR does not exist: %s", PERSONAS_DIR)
        return brand_rules, content_rules, agent_seeds

    for path in sorted(PERSONAS_DIR.glob("*.md")):
        agent_id = path.stem  # filename without .md
        try:
            fm, body = parse_persona_file(path)
        except Exception as e:
            logger.error("Failed to parse %s: %s", path, e)
            continue

        agent_type = fm.get("agent_type", "demand")
        organization = fm.get("organization") or fm.get("brand") or fm.get("service") or agent_id

        if agent_type == "demand":
            rules = _build_brand_rules(agent_id, fm, body)
            brand_rules[agent_id] = rules
            agent_seeds.append({
                "agent_id": agent_id,
                "agent_type": "demand",
                "organization": organization,
                "agent_name": rules.agent_name,
                "description": body,
            })
        elif agent_type == "supply":
            rules = _build_content_rules(agent_id, fm, body)
            content_rules[agent_id] = rules
            agent_seeds.append({
                "agent_id": agent_id,
                "agent_type": "supply",
                "organization": organization,
                "agent_name": rules.agent_name,
                "description": body,
            })
        else:
            logger.warning("Unknown agent_type %r in %s — skipping", agent_type, path)

    logger.info(
        "Loaded personas: %d brand, %d content from %s",
        len(brand_rules), len(content_rules), PERSONAS_DIR,
    )
    return brand_rules, content_rules, agent_seeds
