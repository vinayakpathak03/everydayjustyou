import asyncio
import json
import uuid
from functools import lru_cache

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from google import genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db as get_rls_scoped_db
from app.integrations.storage import get_storage_client
from app.models.chat import ChatConversation, ChatMessage
from app.models.garment import GarmentImage
from app.models.outfit import Outfit, OutfitItem
from app.schemas.chat import ChatRequest
from app.services.stylist_service import run_chat_turn

router = APIRouter(prefix="/stylist", tags=["stylist"])


@lru_cache
def _get_client() -> genai.Client:
    return genai.Client(api_key=get_settings().gemini_api_key)


async def _resolve_conversation(
    db: AsyncSession, user_id: uuid.UUID, conversation_id: uuid.UUID | None
) -> ChatConversation:
    if conversation_id is not None:
        existing = (
            await db.execute(select(ChatConversation).where(ChatConversation.id == conversation_id))
        ).scalar_one_or_none()
        if existing is not None:
            return existing
    conversation = ChatConversation(user_id=user_id)
    db.add(conversation)
    await db.flush()
    return conversation


async def _outfit_card_payload(db: AsyncSession, outfit_id: uuid.UUID) -> dict | None:
    outfit = (await db.execute(select(Outfit).where(Outfit.id == outfit_id))).scalar_one_or_none()
    if outfit is None:
        return None
    rows = list(
        (
            await db.execute(
                select(OutfitItem.slot, OutfitItem.garment_id).where(
                    OutfitItem.outfit_id == outfit_id
                )
            )
        ).all()
    )
    garment_ids = [gid for _, gid in rows]
    images: dict[uuid.UUID, str] = {}
    if garment_ids:
        image_rows = list(
            (
                await db.execute(
                    select(GarmentImage.garment_id, GarmentImage.storage_url)
                    .where(GarmentImage.garment_id.in_(garment_ids))
                    .order_by(GarmentImage.is_primary.desc(), GarmentImage.sort_order)
                )
            ).all()
        )
        paths: dict[uuid.UUID, str] = {}
        for gid, url in image_rows:
            paths.setdefault(gid, url)
        # Bucket is private (see storage.py) — sign before this leaves the API.
        signed = await asyncio.to_thread(get_storage_client().signed_urls, list(paths.values()))
        images = {gid: signed.get(path, path) for gid, path in paths.items()}
    return {
        "id": str(outfit.id),
        "score": outfit.score,
        "rationale": outfit.rationale,
        "items": [
            {"slot": slot, "garment_id": str(gid), "image_url": images.get(gid)}
            for slot, gid in rows
        ],
    }


@router.post("/chat")
async def chat(
    body: ChatRequest,
    current: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """Streams the reply as SSE. Note: this chunks the final response text into
    pieces for a streaming feel — it is NOT true Gemini token-level streaming,
    which doesn't compose cleanly with the multi-turn tool-calling loop below
    (a tool call can only be acted on after the model's turn is complete). A
    real token stream is a plausible follow-up once the pure-text case (no
    tool calls needed) is worth optimizing separately from the tool-calling case.
    """
    user_uuid = uuid.UUID(current.id)

    async def event_stream():
        async for db in get_rls_scoped_db(current):
            conversation = await _resolve_conversation(db, user_uuid, body.conversation_id)
            conv_payload = json.dumps({"conversation_id": str(conversation.id)})
            yield f"event: conversation\ndata: {conv_payload}\n\n"

            result = await run_chat_turn(
                db, user_uuid, conversation.id, body.message, _get_client()
            )

            db.add(ChatMessage(conversation_id=conversation.id, role="user", content=body.message))
            db.add(
                ChatMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=result.text,
                    tool_calls={"calls": result.tool_call_log} if result.tool_call_log else None,
                    referenced_garment_ids=result.referenced_garment_ids or None,
                    referenced_outfit_id=result.referenced_outfit_id,
                )
            )
            if conversation.title is None:
                conversation.title = body.message[:80]
            await db.commit()

            words = result.text.split(" ")
            chunk_size = 6
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i : i + chunk_size])
                yield f"event: token\ndata: {json.dumps({'text': chunk + ' '})}\n\n"
                await asyncio.sleep(0.05)

            if result.referenced_outfit_id:
                card = await _outfit_card_payload(db, result.referenced_outfit_id)
                if card:
                    yield f"event: outfit_cards\ndata: {json.dumps({'outfits': [card]})}\n\n"

            yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
