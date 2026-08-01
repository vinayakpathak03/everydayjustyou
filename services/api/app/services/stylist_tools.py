"""The Stylist's fixed toolset — see docs/architecture/system-architecture.md §5.3.
Every tool is grounded in real data: search_wardrobe/generate_outfit only ever
return items that exist in `garments`, and sensitive-category items are excluded
from every tool here exactly as they are from the Outfit Generator (PRD §7.1).
"""

import uuid
from dataclasses import dataclass

from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.chat import OutfitReranker
from app.integrations.weather import WeatherClient
from app.models.garment import Garment
from app.models.user import User
from app.models.wear_log import WearLog
from app.services.outfit_engine import GenerationContext
from app.services.outfit_service import generate_and_persist
from app.services.wear_log_service import log_wear as log_wear_rows

STYLIST_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_wardrobe",
            description=(
                "Search the user's own wardrobe by category, color, and/or occasion. "
                "Returns only items that actually exist in their closet — never assume "
                "an item exists without calling this."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "category": types.Schema(
                        type="STRING",
                        description="top|bottom|dress|outerwear|shoes|bag|accessory|jewelry",
                    ),
                    "primary_color": types.Schema(type="STRING"),
                    "occasion": types.Schema(type="STRING"),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="generate_outfit",
            description="Generate scored outfit suggestions from the user's real wardrobe.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "occasion": types.Schema(type="STRING"),
                    "season": types.Schema(type="STRING"),
                    "count": types.Schema(type="INTEGER"),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="log_wear",
            description="Record that the user is wearing specific garments or an outfit today.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "garment_ids": types.Schema(type="ARRAY", items=types.Schema(type="STRING")),
                    "outfit_id": types.Schema(type="STRING"),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_wear_history",
            description="Look up recent wear history, optionally for one specific garment.",
            parameters=types.Schema(
                type="OBJECT", properties={"garment_id": types.Schema(type="STRING")}
            ),
        ),
        types.FunctionDeclaration(
            name="get_weather",
            description="Get the user's current local weather, if their location is known.",
            parameters=types.Schema(type="OBJECT", properties={}),
        ),
    ]
)


@dataclass
class ToolContext:
    db: AsyncSession
    user_id: uuid.UUID
    reranker: OutfitReranker
    weather_client: WeatherClient


@dataclass
class ToolResult:
    response: dict
    referenced_garment_ids: list[uuid.UUID]
    referenced_outfit_id: uuid.UUID | None = None


async def _search_wardrobe(ctx: ToolContext, args: dict) -> ToolResult:
    stmt = select(Garment).where(
        Garment.user_id == ctx.user_id,
        Garment.is_archived.is_(False),
        Garment.sensitive_category.is_(False),
        Garment.status != "processing",
    )
    if args.get("category"):
        stmt = stmt.where(Garment.category == args["category"])
    if args.get("primary_color"):
        stmt = stmt.where(Garment.primary_color.ilike(f"%{args['primary_color']}%"))
    if args.get("occasion"):
        stmt = stmt.where(Garment.occasion.any(args["occasion"]))
    garments = list((await ctx.db.execute(stmt.limit(10))).scalars())
    return ToolResult(
        response={
            "items": [
                {
                    "id": str(g.id),
                    "category": g.category,
                    "primary_color": g.primary_color,
                    "description": g.ai_description,
                }
                for g in garments
            ]
        },
        referenced_garment_ids=[g.id for g in garments],
    )


async def _generate_outfit(ctx: ToolContext, args: dict) -> ToolResult:
    context = GenerationContext(
        occasion=args.get("occasion"),
        season=args.get("season"),
        count=min(int(args.get("count") or 3), 4),
    )
    results = await generate_and_persist(ctx.db, ctx.user_id, context, ctx.reranker)
    if not results:
        return ToolResult(
            response={"outfits": [], "note": "Not enough tagged wardrobe items to build an outfit"},
            referenced_garment_ids=[],
        )
    garment_ids = [g.id for _, items in results for g in items.values()]
    return ToolResult(
        response={
            "outfits": [
                {
                    "id": str(outfit.id),
                    "score": outfit.score,
                    "rationale": outfit.rationale,
                    "items": [
                        {"slot": slot, "category": g.category, "color": g.primary_color}
                        for slot, g in items.items()
                    ],
                }
                for outfit, items in results
            ]
        },
        referenced_garment_ids=garment_ids,
        referenced_outfit_id=results[0][0].id,
    )


async def _log_wear(ctx: ToolContext, args: dict) -> ToolResult:
    garment_ids = [uuid.UUID(g) for g in args.get("garment_ids") or []]
    outfit_id = uuid.UUID(args["outfit_id"]) if args.get("outfit_id") else None
    logs = await log_wear_rows(ctx.db, ctx.user_id, garment_ids=garment_ids, outfit_id=outfit_id)
    return ToolResult(
        response={"logged": len(logs) > 0, "count": len(logs)},
        referenced_garment_ids=[log.garment_id for log in logs if log.garment_id],
        referenced_outfit_id=outfit_id,
    )


async def _get_wear_history(ctx: ToolContext, args: dict) -> ToolResult:
    stmt = (
        select(WearLog)
        .where(WearLog.user_id == ctx.user_id)
        .order_by(WearLog.worn_on.desc())
        .limit(10)
    )
    if args.get("garment_id"):
        stmt = stmt.where(WearLog.garment_id == uuid.UUID(args["garment_id"]))
    logs = list((await ctx.db.execute(stmt)).scalars())
    return ToolResult(
        response={
            "history": [
                {
                    "garment_id": str(log.garment_id) if log.garment_id else None,
                    "worn_on": str(log.worn_on),
                }
                for log in logs
            ]
        },
        referenced_garment_ids=[log.garment_id for log in logs if log.garment_id],
    )


async def _get_weather(ctx: ToolContext, _args: dict) -> ToolResult:
    user = (await ctx.db.execute(select(User).where(User.id == ctx.user_id))).scalar_one_or_none()
    location = user.location if user else None
    if not location or "lat" not in location or "lng" not in location:
        return ToolResult(
            response={"available": False, "note": "No location set"}, referenced_garment_ids=[]
        )
    weather = await ctx.weather_client.current(location["lat"], location["lng"])
    if weather is None:
        return ToolResult(
            response={"available": False, "note": "Weather service unavailable"},
            referenced_garment_ids=[],
        )
    return ToolResult(response={"available": True, **weather}, referenced_garment_ids=[])


TOOL_DISPATCH = {
    "search_wardrobe": _search_wardrobe,
    "generate_outfit": _generate_outfit,
    "log_wear": _log_wear,
    "get_wear_history": _get_wear_history,
    "get_weather": _get_weather,
}


async def execute_tool(name: str, args: dict, ctx: ToolContext) -> ToolResult:
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        return ToolResult(response={"error": f"unknown tool {name}"}, referenced_garment_ids=[])
    return await handler(ctx, args)
