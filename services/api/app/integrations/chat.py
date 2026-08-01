from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.core.config import get_settings

# A stronger reasoning tier than the bulk-tagging model is acceptable here — this
# is interactive, not batch, and volume is bounded by count (a handful of calls
# per generate request). See docs/tech-stack-justification.md "Design for
# free-tier rate limits explicitly."
RERANK_MODEL = "gemini-2.0-flash"

RERANK_PROMPT = """You are a personal stylist reasoning over outfit combinations
that already exist in someone's real closet. You are given a numbered list of
candidate outfits (each with its actual items and a rule-based score breakdown)
and must select the best {count} of them, ranked. For each selected outfit, write
a warm, confident 1-2 sentence rationale ("why this works") grounded in the
actual items listed — never invent an item, brand, or attribute not given to you.
Also give a qualitative_score from 1-100 reflecting your own judgment of how well
the outfit works, independent of the rule score you were shown."""


class OutfitPick(BaseModel):
    candidate_index: int
    rationale: str
    qualitative_score: int = Field(ge=1, le=100)


class RerankResult(BaseModel):
    picks: list[OutfitPick]


def _describe_candidate(index: int, items: dict, breakdown: dict) -> str:
    item_lines = "\n".join(
        f"  - {slot}: {g.primary_color or 'unknown color'} {g.category}"
        f"{f', {g.subcategory}' if g.subcategory else ''}"
        f"{f' ({g.pattern})' if g.pattern else ''}"
        for slot, g in items.items()
    )
    return (
        f"Candidate {index}:\n{item_lines}\n"
        f"  rule score breakdown: {breakdown}"
    )


class OutfitReranker:
    """Re-ranks and explains — never invents. See system-architecture.md §5.2 step 3:
    'only the top ~10 rule-scored combinations are sent to the LLM ... the LLM
    picks/orders among given candidates and writes the rationale, it does not
    invent new combinations from scratch.'"""

    def __init__(self, client: genai.Client) -> None:
        self._client = client

    async def rerank(self, candidates: list, count: int) -> RerankResult:
        descriptions = "\n\n".join(
            _describe_candidate(i, c.items, c.breakdown) for i, c in enumerate(candidates)
        )
        response = await self._client.aio.models.generate_content(
            model=RERANK_MODEL,
            contents=[
                RERANK_PROMPT.format(count=count),
                f"\n\nCandidates:\n\n{descriptions}",
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RerankResult,
            ),
        )
        return RerankResult.model_validate_json(response.text)


@lru_cache
def get_outfit_reranker() -> OutfitReranker:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    return OutfitReranker(client)
