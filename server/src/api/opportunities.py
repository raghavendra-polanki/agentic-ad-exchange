"""Opportunity signaling and proposal submission API routes."""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.api.deps import get_current_agent
from src.engine.orchestrator import (
    handle_pass_opportunity,
    handle_select_winner,
    handle_signal_opportunity,
    handle_submit_proposal,
)
from src.schemas.opportunities import OpportunitySignal
from src.schemas.proposals import Proposal
from src.store import store

router = APIRouter()

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@router.post("/")
async def signal_opportunity(
    signal: OpportunitySignal,
    agent=Depends(get_current_agent),
):
    """Supply agent signals a new opportunity on the exchange."""
    return await handle_signal_opportunity(agent, signal)


@router.post("/with-image")
async def signal_opportunity_with_image(
    image: UploadFile = File(...),
    signal_json: str = Form(...),
    agent=Depends(get_current_agent),
):
    """Supply agent signals an opportunity with an image for scene analysis.

    Accepts multipart/form-data with:
    - image: the athlete/moment image file
    - signal_json: JSON string of OpportunitySignal fields
    """
    signal = OpportunitySignal(**json.loads(signal_json))

    # Save image locally
    image_id = uuid.uuid4().hex[:12]
    ext = image.filename.rsplit(".", 1)[-1] if image.filename and "." in image.filename else "jpg"
    save_path = _STATIC_DIR / "opportunities" / f"{image_id}.{ext}"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(await image.read())

    # Attach image reference to signal
    signal.image_id = image_id
    signal.image_url = f"/static/opportunities/{image_id}.{ext}"

    return await handle_signal_opportunity(agent, signal)


@router.post("/signal")
async def signal_from_dashboard(body: dict):
    """Dashboard signals an opportunity on behalf of a supply agent.

    No auth required — this is a dashboard convenience endpoint.
    Body: {agent_id: str, signal: OpportunitySignal dict}
    Optionally include image_url for pre-staged demo images.
    """
    agent_id = body.get("agent_id", "")
    signal_data = body.get("signal", {})

    agent = store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Supply agent not found")

    signal = OpportunitySignal(**signal_data)

    # If image_url points to a demo image, set image_id from filename
    if signal.image_url and not signal.image_id:
        img_path = _STATIC_DIR / signal.image_url.lstrip("/static/")
        if img_path.exists():
            signal.image_id = img_path.stem

    return await handle_signal_opportunity(agent, signal)


@router.post("/analyze-image")
async def analyze_uploaded_image(image: UploadFile = File(...)):
    """Run Gemini Vision on an uploaded moment image and return structured
    form-fill suggestions. Used by the Signal Opportunity page to populate
    athlete / school / sport / description / pricing fields automatically.

    Best-effort — if Gemini is unavailable or returns garbage, returns 200
    with empty fields so the dashboard can fall back gracefully.
    """
    from src.gemini.adaptor import gemini

    image_bytes = await image.read()
    mime = image.content_type or "image/jpeg"

    if not gemini.available:
        return {"ok": False, "reason": "gemini_unavailable", "suggestion": {}}

    prompt = """You are analyzing a sports content image to suggest metadata for an
ad-exchange listing. Be ACCURATE to what's in the image — do not invent details
that aren't visible. If unsure, say so by leaving the field empty.

Return ONLY a single JSON object (no markdown fences, no prose) with these keys:
{
  "athlete_name": "<best guess for the athlete shown, or '' if unknown>",
  "school": "<team or school name visible on jersey/helmet, or '' if unclear>",
  "sport": "<one of: basketball, football, soccer, baseball, track, swimming, hockey, other>",
  "moment_description": "<2-3 sentence vivid description of what's happening, what makes the moment notable, equipment/brand visibility, mood, lighting>",
  "audience_reach": <integer, conservative estimate of how many people would see this clip — 50000 for routine plays, 500000 for highlights, 1500000+ for top SportsCenter plays>,
  "trending_score": <number 0-10, how likely this is to go viral>,
  "min_price": <integer USD, suggested floor price for branded content tied to this moment — 100 for hyperlocal, 1000 for mid-tier college, 5000+ for premium>,
  "content_formats": <array, subset of ["gameday_graphic","social_post","highlight_reel","story","video_clip"]>,
  "confidence": "<low|medium|high — how confident you are in the suggestions>"
}

If you can identify the league (NFL, NBA, college, etc.), include that signal in
moment_description. Do not output anything outside the JSON object."""

    try:
        text = await gemini.analyze(image_bytes, prompt, mime_type=mime)
    except Exception as e:
        return {"ok": False, "reason": str(e), "suggestion": {}}

    # Strip markdown fences if Gemini ignored the instruction
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if "```" in cleaned:
            cleaned = cleaned[: cleaned.rindex("```")]
        cleaned = cleaned.strip()

    try:
        suggestion = json.loads(cleaned[cleaned.index("{"): cleaned.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError) as e:
        return {"ok": False, "reason": f"parse_failed: {e}", "raw": text[:500], "suggestion": {}}

    return {"ok": True, "suggestion": suggestion}


@router.post("/signal-with-image")
async def signal_with_image_from_dashboard(
    image: UploadFile = File(...),
    signal_json: str = Form(...),
    agent_id: str = Form(...),
):
    """Dashboard variant of /with-image — accepts agent_id as a form
    field instead of requiring Bearer-token auth. Used by the
    Signal Opportunity page when the user uploads a custom image.
    """
    agent = store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Supply agent not found")

    try:
        signal_data = json.loads(signal_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signal_json: {e}")

    signal = OpportunitySignal(**signal_data)

    # Save uploaded image
    image_id = uuid.uuid4().hex[:12]
    ext = "jpg"
    if image.filename and "." in image.filename:
        ext = image.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: .{ext}")

    save_path = _STATIC_DIR / "opportunities" / f"{image_id}.{ext}"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(await image.read())

    signal.image_id = image_id
    signal.image_url = f"/static/opportunities/{image_id}.{ext}"

    return await handle_signal_opportunity(agent, signal)


@router.post("/{opportunity_id}/propose")
async def submit_proposal(
    opportunity_id: str,
    proposal: Proposal,
    agent=Depends(get_current_agent),
):
    """Demand agent submits a proposal for an opportunity."""
    result = await handle_submit_proposal(agent, opportunity_id, proposal)
    if result is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return result


@router.post("/{opportunity_id}/pass")
async def pass_opportunity(
    opportunity_id: str,
    body: dict | None = None,
    agent=Depends(get_current_agent),
):
    """Demand agent declines an opportunity. Optional body: {"reasoning": str}"""
    reasoning = (body or {}).get("reasoning", "")
    result = await handle_pass_opportunity(agent, opportunity_id, reasoning)
    if result is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return result


@router.post("/{opportunity_id}/select-winner")
async def select_winner(
    opportunity_id: str,
    agent=Depends(get_current_agent),
):
    """Select the best proposal for an opportunity."""
    result = await handle_select_winner(opportunity_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return result
