import io
from functools import lru_cache
from typing import Protocol

from PIL import Image
from rembg import new_session, remove


class BackgroundRemover(Protocol):
    def remove(self, image_bytes: bytes) -> bytes: ...


@lru_cache
def _session():
    # u2netp (~4.7MB) rather than the full u2net (~176MB) — deliberately the
    # smaller/faster model given Render/Railway free-tier RAM constraints (see
    # docs/tech-stack-justification.md). Slightly lower edge-quality than u2net,
    # judged an acceptable trade for staying comfortably inside free-tier memory.
    return new_session("u2netp")


class RembgBackgroundRemover:
    """Self-hosted, no per-image cost — see BackgroundRemover interface note in
    docs/architecture/system-architecture.md §2. Runs synchronously (CPU-bound);
    the caller (app/workers/jobs/process_image.py) is responsible for running
    this off the event loop via asyncio.to_thread."""

    def remove(self, image_bytes: bytes) -> bytes:
        output = remove(image_bytes, session=_session())
        # `remove()` already returns PNG bytes with an alpha channel, but we
        # round-trip through Pillow to normalize mode/format defensively (some
        # inputs — e.g. CMYK JPEGs — otherwise produce a subtly malformed PNG).
        image = Image.open(io.BytesIO(output)).convert("RGBA")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
