"""GeminiAdaptor — core client for Gemini Vision, Reasoning, and Image Generation.

Ported from Pixology's Node.js GeminiAdaptor pattern. Uses google-genai Python SDK.
Supports:
  - analyze(): multimodal vision (image + prompt → structured text)
  - analyze_stream(): streamed reasoning with thinking visible
  - generate_image(): image generation with reference images
"""

import asyncio
import base64
import functools
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger("aax.gemini")

# Load env
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-3-flash-preview")
GEMINI_REASONING_MODEL = os.getenv("GEMINI_REASONING_MODEL", "gemini-3-flash-preview")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")


class GeminiAdaptor:
    """Unified Gemini client for AAX platform agent and participant agents."""

    def __init__(self, api_key: str | None = None):
        key = api_key or GEMINI_API_KEY
        if not key:
            logger.warning("No GEMINI_API_KEY set — Gemini calls will fail")
        self.client = genai.Client(api_key=key) if key else None
        self.vision_model = GEMINI_VISION_MODEL
        self.reasoning_model = GEMINI_REASONING_MODEL
        self.image_model = GEMINI_IMAGE_MODEL

    @property
    def available(self) -> bool:
        return self.client is not None

    async def analyze(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        model: str | None = None,
    ) -> str:
        """Send image + prompt to Gemini Vision, return text response."""
        if not self.client:
            raise RuntimeError("Gemini client not initialized (missing API key)")

        model_id = model or self.vision_model
        start = time.time()

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=model_id,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4096,
            ),
        )

        text = response.text or ""
        duration = time.time() - start
        logger.info("Gemini analyze: model=%s, %d chars in %.1fs", model_id, len(text), duration)
        return text

    async def analyze_stream(
        self,
        image_bytes: bytes,
        prompt: str,
        on_thought: Callable | None = None,
        on_content: Callable | None = None,
        mime_type: str = "image/jpeg",
        model: str | None = None,
        thinking_budget: int = 8192,
    ) -> dict:
        """Stream reasoning with thoughts visible. Returns {text, thoughts}.

        Runs the blocking Gemini stream in a thread to avoid blocking
        the event loop, then fires async callbacks with collected chunks.
        """
        if not self.client:
            raise RuntimeError("Gemini client not initialized (missing API key)")

        model_id = model or self.reasoning_model
        start = time.time()

        # Run blocking stream in thread, collect chunks
        def _run_stream():
            thought_chunks = []
            content_chunks = []
            stream = self.client.models.generate_content_stream(
                model=model_id,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    types.Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=thinking_budget,
                    ),
                ),
            )
            for chunk in stream:
                parts = chunk.candidates[0].content.parts if chunk.candidates else []
                for part in parts:
                    if not part.text:
                        continue
                    if part.thought:
                        thought_chunks.append(part.text)
                    else:
                        content_chunks.append(part.text)
            return thought_chunks, content_chunks

        thought_chunks, content_chunks = await asyncio.to_thread(_run_stream)

        # Fire async callbacks with collected chunks
        full_thoughts = ""
        for chunk in thought_chunks:
            full_thoughts += chunk
            if on_thought:
                await on_thought(chunk)

        full_text = ""
        for chunk in content_chunks:
            full_text += chunk
            if on_content:
                await on_content(chunk)

        duration = time.time() - start
        logger.info(
            "Gemini stream: model=%s, thoughts=%d chars, content=%d chars, %.1fs",
            model_id, len(full_thoughts), len(full_text), duration,
        )

        return {"text": full_text, "thoughts": full_thoughts}

    async def reason(
        self,
        prompt: str,
        on_thought: Callable | None = None,
        on_content: Callable | None = None,
        model: str | None = None,
        thinking_budget: int = 8192,
        image_bytes: bytes | None = None,
        mime_type: str = "image/jpeg",
    ) -> dict:
        """Text-only or multimodal reasoning with streamed thoughts.

        Runs blocking stream in a thread, then fires async callbacks.
        """
        if not self.client:
            raise RuntimeError("Gemini client not initialized (missing API key)")

        model_id = model or self.reasoning_model
        start = time.time()

        contents = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        contents.append(types.Part.from_text(text=prompt))

        def _run_stream():
            thought_chunks = []
            content_chunks = []
            stream = self.client.models.generate_content_stream(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=thinking_budget,
                    ),
                ),
            )
            for chunk in stream:
                parts = chunk.candidates[0].content.parts if chunk.candidates else []
                for part in parts:
                    if not part.text:
                        continue
                    if part.thought:
                        thought_chunks.append(part.text)
                    else:
                        content_chunks.append(part.text)
            return thought_chunks, content_chunks

        thought_chunks, content_chunks = await asyncio.to_thread(_run_stream)

        full_thoughts = ""
        for chunk in thought_chunks:
            full_thoughts += chunk
            if on_thought:
                await on_thought(chunk)

        full_text = ""
        for chunk in content_chunks:
            full_text += chunk
            if on_content:
                await on_content(chunk)

        duration = time.time() - start
        logger.info(
            "Gemini reason: %.1fs, thoughts=%d, content=%d",
            duration, len(full_thoughts), len(full_text),
        )
        return {"text": full_text, "thoughts": full_thoughts}

    async def generate_image(
        self,
        prompt: str,
        reference_images: list[tuple[bytes, str]] | None = None,
        aspect_ratio: str = "16:9",
        model: str | None = None,
    ) -> bytes | None:
        """Generate an image with optional reference images.

        Uses PIL Image objects as input (per Gemini docs) and
        part.as_image() for output extraction.

        Args:
            prompt: Generation prompt
            reference_images: List of (image_bytes, mime_type) tuples
            aspect_ratio: Output aspect ratio
            model: Model override

        Returns:
            Generated image bytes (PNG) or None on failure
        """
        from PIL import Image
        import io

        if not self.client:
            raise RuntimeError("Gemini client not initialized (missing API key)")

        model_id = model or self.image_model
        start = time.time()

        # Build contents: reference images as PIL Images + text prompt
        contents = []
        if reference_images:
            for img_bytes, _mime in reference_images:
                try:
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    contents.append(pil_img)
                    logger.info("Image gen: added reference image %dx%d", pil_img.width, pil_img.height)
                except Exception as e:
                    logger.warning("Failed to open reference image: %s", e)
        contents.append(prompt)

        logger.info(
            "Image gen REQUEST: model=%s, prompt=%s, ref_images=%d",
            model_id, prompt[:120], len(reference_images or []),
        )

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

            # Log full response structure
            logger.info(
                "Image gen RESPONSE: candidates=%d, parts=%d",
                len(response.candidates) if response.candidates else 0,
                len(response.parts) if response.parts else 0,
            )

            for i, part in enumerate(response.parts):
                logger.info(
                    "  Part %d: inline_data=%s, text=%s",
                    i,
                    bool(part.inline_data),
                    repr(part.text[:100]) if part.text else None,
                )
                if part.inline_data is not None:
                    genai_image = part.as_image()
                    image_bytes = genai_image.image_bytes
                    if image_bytes:
                        duration = time.time() - start
                        logger.info(
                            "Image gen SUCCESS: model=%s, %.1fs, %d bytes",
                            model_id, duration, len(image_bytes),
                        )
                        return image_bytes
                    else:
                        logger.warning("  Part %d: inline_data present but image_bytes is empty", i)

            logger.warning("Image gen: no image in response (all parts were text)")
            return None

        except Exception as e:
            logger.error("Image gen FAILED: %s: %s", type(e).__name__, e)
            return None

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Simple text generation (no streaming, no thinking)."""
        if not self.client:
            raise RuntimeError("Gemini client not initialized (missing API key)")

        model_id = model or self.reasoning_model
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=model_id,
            contents=[types.Part.from_text(text=prompt)],
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text or ""


# Singleton instance
gemini = GeminiAdaptor()
