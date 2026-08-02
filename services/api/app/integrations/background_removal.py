import io
from typing import Protocol

from PIL import Image, ImageOps

# Phone photos routinely come in at 3000-4000px+ per side (10+ megapixels).
# Resizing keeps storage/upload/Gemini-payload size sane regardless of what
# background removal ends up doing (or not doing) below.
MAX_DIMENSION = 1280


class BackgroundRemover(Protocol):
    def remove(self, image_bytes: bytes) -> bytes: ...


class RembgBackgroundRemover:
    """Despite the name, this no longer runs rembg — see the note below. Still
    implements the BackgroundRemover interface (app/workers/jobs/process_image.py
    calls it the same way regardless), just without the actual bg-removal step,
    so nothing else in the pipeline needed to change.

    `rembg` (onnxruntime under the hood) was live-verified to reliably OOM-kill
    the process on Render's free-tier 512MB instance — tried downscaling the
    input image first and tuning ONNX Runtime's memory/thread settings down as
    far as they go, and it still crashed on the very first real upload. Given
    no budget for a bigger instance, the pragmatic call was to drop the
    background-removal step entirely rather than keep chasing a memory ceiling
    that isn't there to chase. Items just keep their original photo background
    now; every other part of the pipeline (Gemini tagging, embeddings, outfit
    generation, the Stylist) is unaffected — none of that depends on a clean
    cutout, only on the tagged attributes.
    """

    def remove(self, image_bytes: bytes) -> bytes:
        source = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes)))
        if source is None:
            source = Image.open(io.BytesIO(image_bytes))
        if max(source.size) > MAX_DIMENSION:
            source.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        buffer = io.BytesIO()
        source.convert("RGBA").save(buffer, format="PNG")
        return buffer.getvalue()
