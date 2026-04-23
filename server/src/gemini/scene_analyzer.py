"""SceneAnalyzer — Platform Agent's visual intelligence.

Analyzes uploaded athlete images to detect:
- Scene type and mood
- Brand placement zones (with tiers)
- Category recommendations for demand matching
- Pricing guidance per tier
"""

import json
import logging
from collections.abc import Callable

from src.gemini.adaptor import gemini

logger = logging.getLogger("aax.scene_analyzer")

SCENE_ANALYSIS_PROMPT = """You are the AAX Platform Creative Director — an AI that designs branded content placements for sports images.

IMPORTANT: You are NOT suggesting traditional sponsorship (jersey patches, shoe deals, glove logos). Those are handled by contracts, not content creation. Instead, you are suggesting CREATIVE DIGITAL CONTENT placements — ways a brand can be visually integrated into this image through graphic design, compositing, and creative direction.

Think like a creative agency art director: how would you add a brand's identity to this image in a way that looks stunning, shareable, and on-brand?

## Placement Tiers (Creative Content, NOT Physical Sponsorship)

- Tier 1 (Brand Overlay): Brand logo, watermark, or tagline overlaid on the image. Clean graphic design placement — corner logo, bottom bar, or stylized frame. Easy to produce, subtle presence.
  Examples: Nike swoosh in corner with "Just Do It" text, branded border/frame, logo watermark

- Tier 2 (Scene Enhancement): Brand elements composited INTO the scene as if they belong there. Digital signage, LED boards, branded environmental elements that look like they're part of the venue.
  Examples: Brand logo on the scoreboard/jumbotron, digital banner behind the athlete, branded court/field graphics, glowing brand elements in the background

- Tier 3 (Immersive Integration): Brand creatively woven into the scene as a dramatic 3D element. The brand becomes PART of the visual story — cinematic, eye-catching, impossible to miss.
  Examples: Giant 3D brand logo emerging from the floor behind the athlete, brand-colored energy/aura effect around the player, product dramatically placed in the foreground with depth-of-field, brand elements integrated into the action (trails, particles, lighting effects in brand colors)

## What to Analyze
1. Scene type and mood
2. Sport and context
3. Creative opportunities — WHERE in this specific image could brand content be placed for maximum visual impact?
4. What brand categories match this scene's energy and audience?
5. Suggest 3-4 specific creative placements across tiers

Respond with ONLY a JSON object (no markdown):
{
  "scene_type": "athletic_action",
  "mood": "triumph",
  "sport": "basketball",
  "athlete_visibility": {
    "face_clear": true,
    "full_body": true,
    "jersey_visible": true,
    "footwear_visible": true
  },
  "brand_zones": [
    {
      "zone_id": "corner_overlay",
      "description": "Brand logo and tagline in lower-right with semi-transparent treatment, like a broadcast sponsor bug",
      "tier": 1,
      "placement_type": "brand_overlay",
      "feasibility": "high",
      "natural_fit_score": 90
    },
    {
      "zone_id": "background_led_board",
      "description": "Digital LED board behind the athlete composited with brand messaging and colors",
      "tier": 2,
      "placement_type": "scene_enhancement",
      "feasibility": "high",
      "natural_fit_score": 88
    },
    {
      "zone_id": "3d_floor_logo",
      "description": "Giant 3D brand logo emerging from the court surface behind the athlete, with dramatic lighting and brand-colored glow effects",
      "tier": 3,
      "placement_type": "immersive_integration",
      "feasibility": "medium",
      "natural_fit_score": 95
    }
  ],
  "categories": ["sportswear", "energy_drinks", "technology", "automotive"],
  "pricing_guidance": {
    "tier_1_range": [500, 1000],
    "tier_2_range": [1500, 3000],
    "tier_3_range": [4000, 8000]
  },
  "creative_notes": "Describe what makes this image special and how brands could leverage its visual energy."
}"""


class SceneAnalyzer:
    """Analyzes images for brand placement opportunities."""

    async def analyze(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        on_thought: Callable | None = None,
    ) -> dict:
        """Analyze an image for brand placement opportunities.

        Args:
            image_bytes: Raw image data
            mime_type: Image MIME type
            on_thought: Optional callback for streaming thoughts to dashboard

        Returns:
            Parsed SceneAnalysis dict, or fallback on parse failure
        """
        if not gemini.available:
            logger.warning("Gemini not available — returning mock scene analysis")
            return self._mock_analysis()

        try:
            # Use streaming with thoughts so we can show platform "thinking" in dashboard
            result = await gemini.analyze_stream(
                image_bytes=image_bytes,
                prompt=SCENE_ANALYSIS_PROMPT,
                on_thought=on_thought,
                mime_type=mime_type,
                thinking_budget=4096,  # Medium depth for analysis
            )

            # Parse JSON from response
            text = result["text"].strip()
            # Handle potential markdown wrapping
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                elif "```" in text:
                    text = text[:text.rindex("```")]
            text = text.strip()

            analysis = json.loads(text)
            logger.info(
                "Scene analysis complete: type=%s, zones=%d, categories=%s",
                analysis.get("scene_type"),
                len(analysis.get("brand_zones", [])),
                analysis.get("categories"),
            )
            return analysis

        except json.JSONDecodeError as e:
            logger.error("Failed to parse scene analysis JSON: %s", e)
            logger.debug("Raw response: %s", result.get("text", "")[:500] if result else "")
            return self._mock_analysis()
        except Exception as e:
            logger.error("Scene analysis failed: %s", e)
            return self._mock_analysis()

    def _mock_analysis(self) -> dict:
        """Fallback mock analysis when Gemini is unavailable."""
        return {
            "scene_type": "athletic_action",
            "mood": "triumph",
            "sport": "basketball",
            "athlete_visibility": {
                "face_clear": True,
                "full_body": True,
                "jersey_visible": True,
                "footwear_visible": True,
            },
            "brand_zones": [
                {
                    "zone_id": "corner_overlay",
                    "description": "Brand logo and tagline overlay in lower-right corner",
                    "tier": 1,
                    "placement_type": "brand_overlay",
                    "feasibility": "high",
                    "natural_fit_score": 90,
                },
                {
                    "zone_id": "background_led",
                    "description": "Digital LED board behind athlete composited with brand messaging",
                    "tier": 2,
                    "placement_type": "scene_enhancement",
                    "feasibility": "high",
                    "natural_fit_score": 85,
                },
                {
                    "zone_id": "3d_floor_logo",
                    "description": "Giant 3D brand logo on court surface with dramatic glow effects",
                    "tier": 3,
                    "placement_type": "immersive_integration",
                    "feasibility": "medium",
                    "natural_fit_score": 95,
                },
            ],
            "categories": ["sportswear", "energy_drinks", "technology"],
            "pricing_guidance": {
                "tier_1_range": [500, 1000],
                "tier_2_range": [1500, 3000],
                "tier_3_range": [4000, 8000],
            },
            "creative_notes": "Dynamic athletic action shot with strong visual energy for creative brand integration.",
        }


# Singleton
scene_analyzer = SceneAnalyzer()
