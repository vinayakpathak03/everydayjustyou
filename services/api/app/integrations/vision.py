from functools import lru_cache
from typing import Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import get_settings

# Cheapest/fastest Gemini tier for bulk background tagging — see
# docs/tech-stack-justification.md "Design for free-tier rate limits explicitly."
ATTRIBUTE_MODEL = "gemini-2.0-flash"

ATTRIBUTE_EXTRACTION_PROMPT = """You are cataloguing a single clothing item from a
photo for a digital wardrobe app. Extract structured attributes as JSON matching
the given schema. Only describe what's visible in the image — never guess a
brand or invent details you can't see. If uncertain about fabric, say so via
fabric_confidence: "low" rather than guessing confidently."""


class AttributeExtraction(BaseModel):
    """Mirrors the JSON contract in docs/architecture/system-architecture.md §5.1."""

    category: str
    subcategory: str | None = None
    primary_color: str
    secondary_colors: list[str] = []
    pattern: str
    fabric_guess: str | None = None
    fabric_confidence: str = "low"
    sleeve_length: str | None = None
    neckline: str | None = None
    fit: str | None = None
    season: list[str] = []
    occasion: list[str] = []
    formality_score: int
    description: str


class AttributeExtractor(Protocol):
    async def extract(self, image_bytes: bytes, mime_type: str) -> AttributeExtraction: ...


class GeminiAttributeExtractor:
    """Zero-shot structured extraction — see docs/architecture/system-architecture.md
    §5.1 for why this replaces a custom-trained classifier. Never called for
    sensitive-category items; see app/workers/jobs/process_image.py."""

    def __init__(self, client: genai.Client) -> None:
        self._client = client

    async def extract(self, image_bytes: bytes, mime_type: str) -> AttributeExtraction:
        response = await self._client.aio.models.generate_content(
            model=ATTRIBUTE_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ATTRIBUTE_EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AttributeExtraction,
            ),
        )
        return AttributeExtraction.model_validate_json(response.text)


@lru_cache
def get_attribute_extractor() -> GeminiAttributeExtractor:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    return GeminiAttributeExtractor(client)
