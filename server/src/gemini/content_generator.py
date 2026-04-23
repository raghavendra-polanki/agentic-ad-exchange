"""ContentGenerator — Platform Agent's creative output.

Generates branded image options after a deal is agreed.
Uses Gemini image generation with reference images (original + brand assets).
"""

import logging
import uuid
from pathlib import Path

from src.gemini.adaptor import gemini

logger = logging.getLogger("aax.content_generator")

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


def _build_generation_prompt(
    brand_name: str,
    tier: int,
    zone_description: str,
    brand_colors: list[str] | None = None,
    creative_notes: str = "",
    variation: str = "balanced",
) -> str:
    """Build the image generation prompt for a specific tier/zone."""

    tier_descriptions = {
        1: "Brand Overlay — Add the brand logo, tagline, or watermark as a clean graphic overlay on the image. Think broadcast-style sponsor bug, branded frame, or corner logo with tagline. The brand should be clearly readable but not dominate the athlete.",
        2: "Scene Enhancement — Composite brand elements INTO the scene digitally. Add brand logos on scoreboards, LED boards, digital banners in the background, branded court/field graphics, or environmental brand elements that look like they belong in the venue. Make it look like the brand was always there.",
        3: "Immersive Integration — Make the brand a DRAMATIC part of the visual story. Add a giant 3D brand logo emerging from the surface, brand-colored energy effects or aura around the athlete, cinematic brand particles or lighting in brand colors, or a bold foreground product placement with depth-of-field blur. This should be eye-catching and impossible to miss — think movie poster meets sports photography.",
    }

    variation_guidance = {
        "subtle": "Keep brand presence clean and minimal — small logo placement, muted brand colors. The athlete is the hero, brand is the quiet supporter.",
        "balanced": "Clear brand visibility integrated naturally. Logo is noticeable, brand colors are present but harmonize with the scene. Professional broadcast quality.",
        "prominent": "Bold, cinematic brand presence. Large logo, vivid brand colors, dramatic effects. The brand shares the spotlight with the athlete. Think Super Bowl ad quality.",
    }

    colors_str = f"Brand colors: {', '.join(brand_colors)}" if brand_colors else ""

    return f"""Create a branded sports content image for {brand_name}.

You are given a reference sports photograph. Create a NEW version of this image with {brand_name} branding creatively integrated.

## Creative Direction
Tier: {tier} — {tier_descriptions.get(tier, tier_descriptions[3])}
Specific placement: {zone_description}
Style intensity: {variation_guidance.get(variation, variation_guidance['balanced'])}

## Brand: {brand_name}
{colors_str}

## CRITICAL Requirements
- Keep the athlete, their pose, expression, and the action moment intact
- The brand integration should look PROFESSIONALLY DESIGNED — like a real sports marketing agency created it
- Do NOT just paste a logo — integrate it creatively with the scene's lighting, perspective, and energy
- The final image should look like premium social media content that a sports brand would actually post
- Make the {brand_name} branding clearly visible and recognizable

## Creative Notes
{creative_notes}

Generate one high-quality branded sports content image."""


class ContentGenerator:
    """Generates branded image options using Gemini."""

    async def generate_options(
        self,
        original_image_bytes: bytes,
        brand_logo_bytes: bytes | None,
        brand_name: str,
        tier: int,
        zone_description: str,
        brand_colors: list[str] | None = None,
        creative_notes: str = "",
        num_options: int = 3,
        original_mime: str = "image/jpeg",
    ) -> list[dict]:
        """Generate multiple branded image options.

        Args:
            original_image_bytes: The original athlete image
            brand_logo_bytes: Brand logo (optional, used as reference)
            brand_name: Brand name
            tier: Placement tier (1, 2, or 3)
            zone_description: Description of where brand goes
            brand_colors: List of brand color hex codes
            creative_notes: Additional creative direction
            num_options: Number of variations to generate (default 3)
            original_mime: MIME type of original image

        Returns:
            List of {option_id, image_path, image_url, style, description}
        """
        if not gemini.available:
            logger.warning("Gemini not available — returning mock options")
            return self._mock_options(num_options)

        # Prefer "prominent" style for single-option generation
        all_variations = ["prominent", "balanced", "subtle"]
        variations = all_variations[:num_options]
        options = []

        for i, variation in enumerate(variations):
            option_id = i + 1
            logger.info(
                "Generating option %d/%d: %s for %s (Tier %d)",
                option_id, num_options, variation, brand_name, tier,
            )

            prompt = _build_generation_prompt(
                brand_name=brand_name,
                tier=tier,
                zone_description=zone_description,
                brand_colors=brand_colors,
                creative_notes=creative_notes,
                variation=variation,
            )

            # Build reference images
            reference_images = [(original_image_bytes, original_mime)]
            if brand_logo_bytes:
                reference_images.append((brand_logo_bytes, "image/png"))

            try:
                image_bytes = await gemini.generate_image(
                    prompt=prompt,
                    reference_images=reference_images,
                    aspect_ratio="16:9",
                )

                if image_bytes:
                    # Save to local static directory
                    filename = f"gen_{uuid.uuid4().hex[:8]}_{variation}.png"
                    save_path = STATIC_DIR / "generated" / filename
                    save_path.write_bytes(image_bytes)

                    options.append({
                        "option_id": option_id,
                        "image_path": str(save_path),
                        "image_url": f"/static/generated/{filename}",
                        "style": variation,
                        "description": f"{brand_name} — Tier {tier} {variation} placement",
                    })
                    logger.info("Option %d generated: %s", option_id, filename)
                else:
                    logger.warning("Option %d: no image returned", option_id)
                    options.append(self._placeholder_option(option_id, variation, brand_name, tier))

            except Exception as e:
                logger.error("Option %d generation failed: %s", option_id, e)
                options.append(self._placeholder_option(option_id, variation, brand_name, tier))

        return options

    def _placeholder_option(
        self, option_id: int, variation: str, brand_name: str, tier: int,
    ) -> dict:
        """Return a placeholder when generation fails."""
        return {
            "option_id": option_id,
            "image_path": None,
            "image_url": None,
            "style": variation,
            "description": f"{brand_name} — Tier {tier} {variation} (generation pending)",
            "placeholder": True,
        }

    def _mock_options(self, num_options: int) -> list[dict]:
        """Mock options when Gemini is unavailable."""
        # Prefer "prominent" style for single-option generation
        all_variations = ["prominent", "balanced", "subtle"]
        variations = all_variations[:num_options]
        return [
            {
                "option_id": i + 1,
                "image_path": None,
                "image_url": None,
                "style": var,
                "description": f"Mock branded option — {var} style",
                "placeholder": True,
            }
            for i, var in enumerate(variations)
        ]


# Singleton
content_generator = ContentGenerator()
