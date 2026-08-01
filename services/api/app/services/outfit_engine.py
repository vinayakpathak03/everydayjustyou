"""Hybrid rule-based + LLM outfit generation engine — see
docs/architecture/system-architecture.md §5.2. This module is the deterministic
half: candidate retrieval + compatibility scoring. The LLM re-ranking/rationale
step lives in app/integrations/chat.py and is applied on top of this module's
output, never instead of it — the rule engine is what keeps scores explainable
and prevents the LLM from ever inventing an item that isn't actually owned.
"""

import itertools
import random
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from app.models.garment import Garment
from app.services.color import outfit_color_harmony

REQUIRED_SLOTS = ("shoes",)
OPTIONAL_SLOTS = ("outerwear", "bag", "accessory", "jewelry")

MAX_BASES = 40  # capped top+bottom / dress combinations considered
MAX_SHOES_SAMPLED = 8
MAX_RESULTS_CONSIDERED = 60  # before final top-K selection


@dataclass
class GenerationContext:
    occasion: str | None = None
    season: str | None = None
    color_preference: str | None = None
    exclude_recently_worn_days: int = 7
    count: int = 3


@dataclass
class OutfitCandidate:
    items: dict[str, Garment]
    score: int
    breakdown: dict[str, float] = field(default_factory=dict)

    def garment_ids(self) -> frozenset[UUID]:
        return frozenset(g.id for g in self.items.values())


def group_by_category(garments: list[Garment]) -> dict[str, list[Garment]]:
    by_category: dict[str, list[Garment]] = {}
    for g in garments:
        by_category.setdefault(g.category, []).append(g)
    return by_category


def _formality_fit(items: list[Garment]) -> float:
    scores = [g.formality_score for g in items if g.formality_score is not None]
    if len(scores) < 2:
        return 75.0
    spread = max(scores) - min(scores)
    return max(0.0, 100.0 - spread * 8)


def _occasion_fit(items: list[Garment], occasion: str | None) -> float:
    if not occasion:
        return 80.0
    matches = 0
    considered = 0
    for g in items:
        if g.occasion:
            considered += 1
            if occasion in g.occasion:
                matches += 1
    if considered == 0:
        return 70.0
    return round((matches / considered) * 100, 1)


def _season_fit(items: list[Garment], season: str | None) -> float:
    if not season:
        return 80.0
    matches = 0
    considered = 0
    for g in items:
        if g.season:
            considered += 1
            if season in g.season:
                matches += 1
    if considered == 0:
        return 70.0
    return round((matches / considered) * 100, 1)


def _novelty(items: list[Garment], last_worn: dict[UUID, date], exclude_days: int) -> float:
    today = date.today()
    scores = []
    for g in items:
        worn_on = last_worn.get(g.id)
        if worn_on is None:
            scores.append(100.0)
            continue
        days_since = (today - worn_on).days
        scores.append(min(100.0, (days_since / max(exclude_days, 1)) * 100))
    return round(sum(scores) / len(scores), 1) if scores else 100.0


def score_combo(
    items: dict[str, Garment], context: GenerationContext, last_worn: dict[UUID, date]
) -> tuple[int, dict[str, float]]:
    garments = list(items.values())
    breakdown = {
        "color_harmony": outfit_color_harmony([g.color_hex for g in garments if g.color_hex]),
        "formality_fit": _formality_fit(garments),
        "occasion_fit": _occasion_fit(garments, context.occasion),
        "weather_fit": _season_fit(garments, context.season),
        "novelty": _novelty(garments, last_worn, context.exclude_recently_worn_days),
    }
    total = (
        breakdown["color_harmony"] * 0.30
        + breakdown["formality_fit"] * 0.25
        + breakdown["occasion_fit"] * 0.20
        + breakdown["weather_fit"] * 0.10
        + breakdown["novelty"] * 0.15
    )
    return round(total), breakdown


def _build_bases(by_category: dict[str, list[Garment]]) -> list[dict[str, Garment]]:
    dresses = by_category.get("dress", [])
    tops = by_category.get("top", [])
    bottoms = by_category.get("bottom", [])

    bases: list[dict[str, Garment]] = [{"dress": d} for d in dresses]
    bases += [{"top": t, "bottom": b} for t, b in itertools.product(tops, bottoms)]

    if len(bases) > MAX_BASES:
        bases = random.sample(bases, MAX_BASES)
    return bases


def _attach_optional_slots(
    base: dict[str, Garment], by_category: dict[str, list[Garment]]
) -> dict[str, Garment]:
    combo = dict(base)
    known_hexes = [g.color_hex for g in combo.values() if g.color_hex]
    for slot in OPTIONAL_SLOTS:
        candidates = by_category.get(slot, [])
        if not candidates:
            continue
        def _harmony_with(g: Garment) -> float:
            hexes = [*known_hexes, g.color_hex] if g.color_hex else known_hexes
            return outfit_color_harmony(hexes)

        best = max(candidates, key=_harmony_with)
        combo[slot] = best
    return combo


def generate_outfits(
    by_category: dict[str, list[Garment]],
    context: GenerationContext,
    last_worn: dict[UUID, date],
) -> list[OutfitCandidate]:
    """Deterministic candidate generation + scoring. Bounded (not exhaustive) —
    see the MAX_* constants — so this stays cheap even on a wardrobe with a few
    hundred items per slot, at the cost of not literally trying every possible
    combination. Reasonable at this product's actual scale (a handful of users,
    hundreds not tens-of-thousands of items each)."""
    shoes = by_category.get("shoes", [])
    if not shoes:
        return []

    bases = _build_bases(by_category)
    if not bases:
        return []

    sampled_shoes = (
        random.sample(shoes, MAX_SHOES_SAMPLED) if len(shoes) > MAX_SHOES_SAMPLED else shoes
    )

    results: list[OutfitCandidate] = []
    seen: set[frozenset[UUID]] = set()
    for base, shoe in itertools.islice(
        itertools.product(bases, sampled_shoes), MAX_RESULTS_CONSIDERED
    ):
        combo = _attach_optional_slots({**base, "shoes": shoe}, by_category)
        score, breakdown = score_combo(combo, context, last_worn)
        candidate = OutfitCandidate(items=combo, score=score, breakdown=breakdown)
        key = candidate.garment_ids()
        if key in seen:
            continue
        seen.add(key)
        results.append(candidate)

    results.sort(key=lambda c: c.score, reverse=True)
    return results
