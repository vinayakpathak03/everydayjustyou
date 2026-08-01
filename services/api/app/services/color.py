"""Rule-based color harmony against a simplified color-wheel model — see
docs/architecture/system-architecture.md §5.2. Deterministic and explainable
(no LLM call), which is the whole point of doing this step in the rule engine
rather than asking Gemini "do these colors match" per pair.
"""

import colorsys

NEUTRAL_SATURATION_THRESHOLD = 0.15


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    hue, lightness, sat = colorsys.rgb_to_hls(r, g, b)
    return hue * 360, sat, lightness


def pairwise_harmony(hex_a: str, hex_b: str) -> float:
    """Returns 0-1. Neutrals (near-grayscale) are treated as compatible with
    anything, matching how people actually dress — a black bag isn't "clashing"
    with a green dress just because they're far apart on the color wheel."""
    try:
        hue_a, sat_a, _ = _hex_to_hsl(hex_a)
        hue_b, sat_b, _ = _hex_to_hsl(hex_b)
    except (ValueError, IndexError):
        return 0.6  # unparsable hex — neutral-ish default rather than penalizing

    if sat_a < NEUTRAL_SATURATION_THRESHOLD or sat_b < NEUTRAL_SATURATION_THRESHOLD:
        return 0.9

    hue_diff = abs(hue_a - hue_b)
    hue_diff = min(hue_diff, 360 - hue_diff)

    if hue_diff <= 30:
        return 0.85  # monochrome/analogous
    if 150 <= hue_diff <= 210:
        return 0.9  # complementary
    if 100 <= hue_diff < 150 or 210 < hue_diff <= 260:
        return 0.6  # triadic-ish — wearable but less classically "matched"
    return 0.4  # everything else reads as a clash


def outfit_color_harmony(hex_colors: list[str]) -> float:
    """Average pairwise harmony across all colors present, scaled 0-100. Returns
    a neutral-ish 70 if fewer than two garments have a known color — not enough
    signal to score, and an outfit shouldn't be penalized for missing metadata."""
    known = [c for c in hex_colors if c]
    if len(known) < 2:
        return 70.0
    pairs = [(known[i], known[j]) for i in range(len(known)) for j in range(i + 1, len(known))]
    scores = [pairwise_harmony(a, b) for a, b in pairs]
    return round((sum(scores) / len(scores)) * 100, 1)
