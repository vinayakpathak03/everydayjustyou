"""The tool-use loop itself — see docs/architecture/system-architecture.md §5.3.

Caveat worth being upfront about: the exact multi-turn function-calling
mechanics here (how a model's function_call turn and the subsequent function
response turn get threaded back into `contents`) follow the documented Gemini
API pattern, but this hasn't been exercised against a live API key in this
environment — there's no way to fully verify the wire format without one. The
loop is wrapped defensively (bounded iterations, broad exception handling with
a graceful fallback reply) specifically because of that uncertainty: a mistake
here should degrade to an apologetic chat message, not a 500.
"""

import logging
import uuid
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.chat import get_outfit_reranker
from app.integrations.weather import get_weather_client
from app.models.chat import ChatMessage
from app.services.stylist_tools import STYLIST_TOOL, ToolContext, execute_tool

logger = logging.getLogger("app.services.stylist")

CHAT_MODEL = "gemini-2.0-flash"
MAX_TOOL_ITERATIONS = 4
HISTORY_LIMIT = 20

STYLIST_SYSTEM_PROMPT = """You are Muse's AI Stylist: warm, direct, a little
playful, opinionated without being pushy — closer to a trusted friend with
great taste than a customer-service bot. Lead with a clear pick and say why,
then offer alternatives, rather than listing options and asking the user to
decide. You are grounded entirely in the user's real wardrobe: use
search_wardrobe and generate_outfit to see what they actually own before
recommending anything — never invent an item, brand, or attribute you weren't
given by a tool. Keep replies to a few sentences unless the user asks for
detail."""


@dataclass
class ChatTurnResult:
    text: str
    tool_call_log: list[dict] = field(default_factory=list)
    referenced_garment_ids: list[uuid.UUID] = field(default_factory=list)
    referenced_outfit_id: uuid.UUID | None = None


async def _load_history(db: AsyncSession, conversation_id: uuid.UUID) -> list[types.Content]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_LIMIT)
    )
    messages = list(reversed((await db.execute(stmt)).scalars().all()))
    role_map = {"user": "user", "assistant": "model"}
    return [
        types.Content(role=role_map[m.role], parts=[types.Part(text=m.content)])
        for m in messages
        if m.role in role_map
    ]


async def run_chat_turn(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user_message: str,
    client: genai.Client,
) -> ChatTurnResult:
    ctx = ToolContext(
        db=db, user_id=user_id, reranker=get_outfit_reranker(), weather_client=get_weather_client()
    )
    contents = await _load_history(db, conversation_id)
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    result = ChatTurnResult(text="")

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            response = await client.aio.models.generate_content(
                model=CHAT_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=STYLIST_SYSTEM_PROMPT,
                    tools=[STYLIST_TOOL],
                ),
            )
            candidate = response.candidates[0]
            parts = candidate.content.parts or []
            function_calls = [p.function_call for p in parts if p.function_call is not None]

            if not function_calls:
                result.text = response.text or "Not sure what to say to that — try rephrasing?"
                return result

            contents.append(candidate.content)
            response_parts = []
            for fc in function_calls:
                args = dict(fc.args) if fc.args else {}
                tool_result = await execute_tool(fc.name, args, ctx)
                result.tool_call_log.append({"name": fc.name, "args": args})
                result.referenced_garment_ids.extend(tool_result.referenced_garment_ids)
                if tool_result.referenced_outfit_id:
                    result.referenced_outfit_id = tool_result.referenced_outfit_id
                response_parts.append(
                    types.Part.from_function_response(name=fc.name, response=tool_result.response)
                )
            contents.append(types.Content(role="user", parts=response_parts))

        result.text = "That took a lot of steps — try asking again, maybe more specifically?"
        return result
    except Exception:  # noqa: BLE001 — a mechanical/API failure must degrade to a reply, not a 500
        logger.exception("Stylist chat turn failed")
        result.text = "Having trouble reaching the stylist brain right now — try again in a moment."
        return result
