"""
Genre detection — Phase 0 of the review pipeline.

v0.8.4: Expanded register taxonomy (added children_juvenile, popular_commercial).
v0.8.3: Expanded to 6 genres (added creative, reflective).
v0.8.2: Now also classifies writer sophistication level and detects
secondary genre for mixed-genre texts. These inform:
- Writer-level calibration (tone, comment gating, feedback depth)
- Mixed-genre routing (running both dimension sets when justified)
"""

import json

GENRE_DETECTION_SYSTEM = """You are a specialist in analysing writing genres and assessing writer sophistication. Your job is to classify an input text by how it is written (not by topic), and to assess the writer's level.

You must output a single JSON object with these keys:

- "genre": one of "argumentative", "analytical", "expository", "narrative", "creative", "reflective", "mixed". Use "mixed" ONLY when the text genuinely resists classification into any single genre — when it blends forms so thoroughly that no single genre captures more than ~50% of what the text does. Most texts with secondary genre elements should still be classified as their primary genre with a secondary_genre noted.
- "secondary_genre": one of "argumentative", "analytical", "expository", "narrative", "creative", "reflective", null. Set this when the text operates in two distinct modes simultaneously (e.g., a memoir that also advances a political argument). Set null if the text is cleanly one genre.
- "secondary_genre_confidence": a number from 0.0 to 1.0 (how strongly the secondary genre is present). Set 0.0 if secondary_genre is null.
- "register": one of "academic", "journalistic", "essayistic", "literary", "technical", "informal", "children_juvenile", "popular_commercial"
- "purpose": one of "persuade", "inform", "analyse", "narrate", "reflect", "entertain"
- "structural_signals": an object with boolean keys: "has_explicit_thesis", "has_numbered_sections", "has_first_person_focus", "has_story_arc", "has_footnotes", "has_non_english_text", "has_quoted_material"
- "writer_level": one of "elite", "accomplished", "developing". Use these criteria:
    - "elite": Published-quality prose by an experienced writer. Distinctive voice, sophisticated argument architecture, masterful command of register, precise and deliberate word choice. The kind of writing that appears in top-tier publications (New Yorker, LRB, Atlantic, n+1, major academic presses). Few if any structural problems — feedback should be architectural and peer-to-peer.
    - "accomplished": Competent, well-organised writing that demonstrates subject knowledge and clear argumentation, but lacks the distinctive voice or structural sophistication of elite work. May have competent but unremarkable prose, solid but unambitious structure, or gaps in argumentative depth. Graduate-level academic work, good journalism, competent policy writing. Feedback should be substantive but more granular than for elite writers.
    - "developing": Writing that shows significant structural, argumentative, or craft weaknesses. May include unclear thesis, poorly marshalled evidence, inconsistent register, logical gaps, or basic organisational problems. Undergraduate work, early-career writing, first drafts. Feedback should be instructional and specific.
- "writer_level_signals": a brief string (under 50 words) explaining the key indicators of the writer level assessment.
- "confidence": a number from 0.0 to 1.0

Base your decisions on genre conventions and craft signals, not topic. Do not output any other text."""


GENRE_DETECTION_USER = """Classify the following text.

---
{essay_text}
---

Remember: base your genre decision on structural and stylistic features, not topic. Assess writer level based on craft, voice, and argumentative sophistication."""


DEFAULT_GENRE_METADATA = {
    "genre": "argumentative",
    "secondary_genre": None,
    "secondary_genre_confidence": 0.0,
    "register": "academic",
    "purpose": "persuade",
    "structural_signals": {
        "has_explicit_thesis": True,
        "has_numbered_sections": False,
        "has_first_person_focus": False,
        "has_story_arc": False,
        "has_footnotes": False,
        "has_non_english_text": False,
        "has_quoted_material": False,
    },
    "writer_level": "accomplished",
    "writer_level_signals": "",
    "confidence": 0.0,
}


def parse_genre_response(text: str) -> dict:
    """Parse genre detection JSON with validation and fallback."""
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[: cleaned.rfind("```")]
            cleaned = cleaned.strip()

        data = json.loads(cleaned)

        valid_genres = {
            "argumentative", "analytical", "expository",
            "narrative", "creative", "reflective", "mixed",
        }
        if data.get("genre") not in valid_genres:
            data["genre"] = "argumentative"

        # Validate secondary genre
        valid_secondary = {"argumentative", "analytical", "expository", "narrative", "creative", "reflective", None}
        if data.get("secondary_genre") not in valid_secondary:
            data["secondary_genre"] = None
        # Ensure secondary != primary
        if data.get("secondary_genre") == data.get("genre"):
            data["secondary_genre"] = None
            data["secondary_genre_confidence"] = 0.0

        data["secondary_genre_confidence"] = float(data.get("secondary_genre_confidence", 0.0))
        data["confidence"] = float(data.get("confidence", 0.5))

        # Validate writer level
        valid_levels = {"elite", "accomplished", "developing"}
        if data.get("writer_level") not in valid_levels:
            data["writer_level"] = "accomplished"

        data["writer_level_signals"] = str(data.get("writer_level_signals", ""))[:200]

        if "structural_signals" not in data or not isinstance(data["structural_signals"], dict):
            data["structural_signals"] = dict(DEFAULT_GENRE_METADATA["structural_signals"])

        return data

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return dict(DEFAULT_GENRE_METADATA)


# ── Mixed-genre routing logic ──────────────────────────────────────

# Threshold: secondary genre must have at least this confidence to trigger mixed-genre mode
MIXED_GENRE_THRESHOLD = 0.55
MIXED_GENRE_THRESHOLD_ELEVATED = 0.65  # Higher bar for creative/reflective to avoid over-triggering


def should_run_mixed_genre(genre_metadata: dict) -> bool:
    """
    Determine whether mixed-genre mode should be activated.

    Returns True when a secondary genre is detected with sufficient
    confidence. This means both primary and secondary dimension sets
    will be run.

    Creative and reflective genres use a higher threshold (0.65) to
    avoid over-triggering on texts with incidental creative/reflective
    qualities.
    """
    secondary = genre_metadata.get("secondary_genre")
    secondary_conf = genre_metadata.get("secondary_genre_confidence", 0.0)

    if not secondary:
        return False

    # Only supported genres can be secondary
    supported = {"argumentative", "analytical", "expository", "narrative", "creative", "reflective"}
    if secondary not in supported:
        return False

    # Elevated threshold for creative/reflective as secondary genres
    primary = genre_metadata.get("genre")
    elevated_genres = {"creative", "reflective"}
    if primary in elevated_genres or secondary in elevated_genres:
        threshold = MIXED_GENRE_THRESHOLD_ELEVATED
    else:
        threshold = MIXED_GENRE_THRESHOLD

    if secondary_conf < threshold:
        return False

    return True
