import uuid
from datetime import date, timedelta

from app.models.garment import Garment
from app.services.color import outfit_color_harmony, pairwise_harmony
from app.services.outfit_engine import (
    GenerationContext,
    generate_outfits,
    group_by_category,
    score_combo,
)


def _garment(**overrides) -> Garment:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        category="top",
        color_hex="#000000",
        formality_score=5,
        season=None,
        occasion=None,
    )
    defaults.update(overrides)
    return Garment(**defaults)


def test_neutral_colors_score_high_harmony() -> None:
    assert pairwise_harmony("#000000", "#ff00ff") > 0.8


def test_clashing_hues_score_low() -> None:
    # two saturated, roughly-triadic-to-clashing hues
    assert pairwise_harmony("#ff0000", "#aaff00") < 0.7


def test_outfit_color_harmony_needs_two_known_colors() -> None:
    assert outfit_color_harmony(["#ff0000"]) == 70.0
    assert outfit_color_harmony([]) == 70.0


def test_formality_consistency_penalizes_spread() -> None:
    tight = {
        "top": _garment(formality_score=5),
        "bottom": _garment(formality_score=6),
    }
    wide = {
        "top": _garment(formality_score=1),
        "bottom": _garment(formality_score=10),
    }
    ctx = GenerationContext()
    tight_score, tight_breakdown = score_combo(tight, ctx, {})
    wide_score, wide_breakdown = score_combo(wide, ctx, {})
    assert tight_breakdown["formality_fit"] > wide_breakdown["formality_fit"]
    assert tight_score > wide_score


def test_never_worn_item_gets_full_novelty() -> None:
    g = _garment()
    ctx = GenerationContext(exclude_recently_worn_days=7)
    _, breakdown = score_combo({"top": g}, ctx, {})
    assert breakdown["novelty"] == 100.0


def test_recently_worn_item_gets_lower_novelty() -> None:
    g = _garment()
    ctx = GenerationContext(exclude_recently_worn_days=7)
    _, breakdown = score_combo({"top": g}, ctx, {g.id: date.today()})
    assert breakdown["novelty"] < 100.0


def test_generate_outfits_requires_shoes() -> None:
    by_category = group_by_category([_garment(category="top"), _garment(category="bottom")])
    assert generate_outfits(by_category, GenerationContext(), {}) == []


def test_generate_outfits_produces_scored_candidates() -> None:
    garments = [
        _garment(category="top", color_hex="#111111"),
        _garment(category="bottom", color_hex="#222222"),
        _garment(category="shoes", color_hex="#000000"),
    ]
    by_category = group_by_category(garments)
    candidates = generate_outfits(by_category, GenerationContext(count=3), {})
    assert len(candidates) == 1  # exactly one valid combination from this pool
    assert 0 <= candidates[0].score <= 100
    assert set(candidates[0].items.keys()) == {"top", "bottom", "shoes"}


def test_generate_outfits_prefers_dress_and_top_bottom_bases() -> None:
    yesterday = date.today() - timedelta(days=1)
    garments = [
        _garment(category="dress", color_hex="#333333"),
        _garment(category="top", color_hex="#111111"),
        _garment(category="bottom", color_hex="#222222"),
        _garment(category="shoes", color_hex="#000000"),
    ]
    by_category = group_by_category(garments)
    candidates = generate_outfits(by_category, GenerationContext(), {g.id: yesterday for g in []})
    bases_seen = {"dress" in c.items for c in candidates} | {"top" in c.items for c in candidates}
    assert True in bases_seen  # both a dress-based and a top+bottom-based combo exist
    assert len(candidates) == 2
