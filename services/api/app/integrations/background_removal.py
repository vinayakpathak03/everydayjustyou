import io
from functools import lru_cache
from typing import Protocol

import onnxruntime as ort
from PIL import Image, ImageOps
from rembg import new_session, remove

# Phone photos routinely come in at 3000-4000px+ per side (10+ megapixels).
# Feeding that straight into rembg means decoding, tensor ops, and full-res
# alpha compositing all scale with input size — on Render's free-tier 512MB
# instance that's enough on its own to OOM-kill the process. Clothing detail
# doesn't need more than this for tagging/display purposes.
MAX_DIMENSION = 1280


class BackgroundRemover(Protocol):
    def remove(self, image_bytes: bytes) -> bytes: ...


@lru_cache
def _session():
    # u2netp (~4.7MB) rather than the full u2net (~176MB) — deliberately the
    # smaller/faster model given Render/Railway free-tier RAM constraints (see
    # docs/tech-stack-justification.md). Slightly lower edge-quality than u2net,
    # judged an acceptable trade for staying comfortably inside free-tier memory.
    #
    # ONNX Runtime's defaults are tuned for throughput, not memory: the CPU
    # memory arena pre-reserves larger chunks for reuse across calls (good on
    # a real server, wasteful for occasional single-image jobs), and thread
    # count defaults to however many CPUs the container *reports*, which can
    # exceed what a fractional-CPU free-tier instance actually has. Both
    # inflate peak RSS well past what one small model genuinely needs — tuned
    # down here after live OOM crashes on Render's 512MB free tier.
    sess_opts = ort.SessionOptions()
    sess_opts.enable_cpu_mem_arena = False
    sess_opts.intra_op_num_threads = 1
    sess_opts.inter_op_num_threads = 1
    return new_session("u2netp", sess_opts=sess_opts)


class RembgBackgroundRemover:
    """Self-hosted, no per-image cost — see BackgroundRemover interface note in
    docs/architecture/system-architecture.md §2. Runs synchronously (CPU-bound);
    the caller (app/workers/jobs/process_image.py) is responsible for running
    this off the event loop via asyncio.to_thread."""

    def remove(self, image_bytes: bytes) -> bytes:
        source = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes)))
        if source is None:
            source = Image.open(io.BytesIO(image_bytes))
        if max(source.size) > MAX_DIMENSION:
            source.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        downscaled = io.BytesIO()
        source.convert("RGB").save(downscaled, format="JPEG", quality=90)

        output = remove(downscaled.getvalue(), session=_session())
        # `remove()` already returns PNG bytes with an alpha channel, but we
        # round-trip through Pillow to normalize mode/format defensively (some
        # inputs — e.g. CMYK JPEGs — otherwise produce a subtly malformed PNG).
        image = Image.open(io.BytesIO(output)).convert("RGBA")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
