from functools import lru_cache
from typing import Protocol

from google import genai

from app.core.config import get_settings

TEXT_EMBEDDING_MODEL = "text-embedding-004"  # 768-dim — matches garment_embeddings.embedding


class EmbeddingStore(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...


class GeminiEmbeddingStore:
    """Text embeddings only for now. Image embeddings (CLIP, `kind=image_clip` in
    garment_embeddings) are deliberately NOT implemented yet: self-hosted CLIP
    needs `torch`, and a torch-loaded CLIP checkpoint routinely uses several
    hundred MB of RAM — a real risk of OOM-killing the whole API process on
    Render/Railway's free tier (typically 512MB-1GB), which also runs rembg and
    the request-handling process in the same container (see
    docs/tech-stack-justification.md "Background Jobs (no Redis)" and
    system-architecture.md §3 for why there's only one process at all here).
    Rather than ship that risk, image-embedding-dependent features (visual
    duplicate detection, "items that look like this") stay unimplemented until
    that's deliberately revisited — e.g. a lighter ONNX-exported CLIP model
    sharing rembg's onnxruntime runtime instead of adding torch, or accepting
    the memory cost with a paid-tier fallback. Text search/matching (Stylist
    semantic search) works fully without it."""

    def __init__(self, client: genai.Client) -> None:
        self._client = client

    async def embed_text(self, text: str) -> list[float]:
        response = await self._client.aio.models.embed_content(
            model=TEXT_EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values


@lru_cache
def get_embedding_store() -> GeminiEmbeddingStore:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    return GeminiEmbeddingStore(client)
