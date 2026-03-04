"""
Shared pipeline utilities for genre-aware essay review.

v0.8.3: Added focus parameter to synthesis prompt injection.
         Supports 6 genres (creative, reflective added).
v0.8.2: Added mixed-genre prompt loading and writer-level calibration
injection into synthesis prompts.

Both orchestrator.py (async/CLI) and server.py (sync/web) use these
functions to load the correct prompts for a detected or overridden genre.
"""

import importlib

try:
    from .config import (
        get_genre_config, get_writer_level_config, DEFAULT_GENRE, SUPPORTED_GENRES,
        DYNAMIC_CONFIDENCE_THRESHOLD, REVIEW_MODE_STANDARD, REVIEW_MODE_DYNAMIC, REVIEW_MODE_HYBRID,
    )
    from .prompts.shared import MASTER_SYSTEM_PROMPT, CALIBRATION_BLOCKS, MIXED_GENRE_SYNTHESIS_BLOCK, get_length_calibration_block
    from .genre_detection import should_run_mixed_genre  # re-export for server/orchestrator
    from .dynamic_criteria import (
        CRITERIA_GENERATION_SYSTEM,
        CRITERIA_GENERATION_USER,
        DYNAMIC_SYNTHESIS_PROMPT,
        DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE,
        HYBRID_SYNTHESIS_BLOCK,
        parse_criteria_response,
        criteria_to_dimension_prompts,
    )
except ImportError:
    from config import (
        get_genre_config, get_writer_level_config, DEFAULT_GENRE, SUPPORTED_GENRES,
        DYNAMIC_CONFIDENCE_THRESHOLD, REVIEW_MODE_STANDARD, REVIEW_MODE_DYNAMIC, REVIEW_MODE_HYBRID,
    )
    from prompts.shared import MASTER_SYSTEM_PROMPT, CALIBRATION_BLOCKS, MIXED_GENRE_SYNTHESIS_BLOCK, get_length_calibration_block
    from genre_detection import should_run_mixed_genre  # re-export for server/orchestrator
    from dynamic_criteria import (
        CRITERIA_GENERATION_SYSTEM,
        CRITERIA_GENERATION_USER,
        DYNAMIC_SYNTHESIS_PROMPT,
        DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE,
        HYBRID_SYNTHESIS_BLOCK,
        parse_criteria_response,
        criteria_to_dimension_prompts,
    )


def load_genre_prompts(genre):
    """
    Load dimension prompts and synthesis prompt for a genre.

    Args:
        genre: Genre key (e.g. "argumentative", "analytical").
               Falls back to DEFAULT_GENRE if unsupported.

    Returns:
        Tuple of (DIMENSION_PROMPTS dict, SYNTHESIS_PROMPT str, genre_used str)
    """
    config = get_genre_config(genre)
    module = importlib.import_module(config["module"])
    genre_used = genre if genre in SUPPORTED_GENRES else DEFAULT_GENRE
    return module.DIMENSION_PROMPTS, module.SYNTHESIS_PROMPT, genre_used


def load_synthesis_system_message(genre):
    """
    Load the synthesis system message for a genre.

    Each genre module may define SYNTHESIS_SYSTEM_MESSAGE. If not present,
    falls back to a sensible default.

    Args:
        genre: Genre key.

    Returns:
        System message string for the synthesis API call.
    """
    config = get_genre_config(genre)
    module = importlib.import_module(config["module"])
    return getattr(
        module,
        "SYNTHESIS_SYSTEM_MESSAGE",
        "You are a senior editor producing a final review of a serious piece of writing. "
        "You combine intellectual rigour with constructive engagement. You write in analytical "
        "prose, not bullet-point checklists. Every observation you make is anchored to specific "
        "text and explains why it matters for the argument's persuasiveness.",
    )


def build_dimension_system_prompt(dimension_prompt_text):
    """Combine master system prompt with a dimension-specific prompt."""
    return f"{MASTER_SYSTEM_PROMPT}\n\n{dimension_prompt_text}"


# ── Mixed-genre support (v0.8.2) ──────────────────────────────────

def load_mixed_genre_prompts(primary_genre, secondary_genre):
    """
    Load dimension prompts from both primary and secondary genres.

    Returns dimension prompts merged from both genre sets, with keys
    prefixed to avoid collision (e.g., "primary:conceptual_coherence",
    "secondary:voice_and_tone").

    Also returns both synthesis prompts for unified synthesis.

    Args:
        primary_genre: Primary genre key.
        secondary_genre: Secondary genre key.

    Returns:
        Dict with keys:
            primary_prompts: DIMENSION_PROMPTS dict for primary genre
            secondary_prompts: DIMENSION_PROMPTS dict for secondary genre
            primary_synthesis: SYNTHESIS_PROMPT for primary genre
            secondary_synthesis: SYNTHESIS_PROMPT for secondary genre
            primary_genre: validated primary genre
            secondary_genre: validated secondary genre
    """
    p_config = get_genre_config(primary_genre)
    s_config = get_genre_config(secondary_genre)

    p_module = importlib.import_module(p_config["module"])
    s_module = importlib.import_module(s_config["module"])

    p_genre = primary_genre if primary_genre in SUPPORTED_GENRES else DEFAULT_GENRE
    s_genre = secondary_genre if secondary_genre in SUPPORTED_GENRES else DEFAULT_GENRE

    return {
        "primary_prompts": p_module.DIMENSION_PROMPTS,
        "secondary_prompts": s_module.DIMENSION_PROMPTS,
        "primary_synthesis": p_module.SYNTHESIS_PROMPT,
        "secondary_synthesis": getattr(s_module, "SYNTHESIS_PROMPT", ""),
        "primary_system_message": load_synthesis_system_message(p_genre),
        "secondary_system_message": load_synthesis_system_message(s_genre),
        "primary_genre": p_genre,
        "secondary_genre": s_genre,
    }


# ── Writer-level calibration (v0.8.2) ─────────────────────────────

def inject_calibration_into_synthesis(synthesis_prompt: str, writer_level: str) -> str:
    """
    Inject writer-level calibration block into a synthesis prompt.

    The calibration block is inserted just before the CRITICAL RULES
    section (or appended before the essay text if no rules section found).

    Args:
        synthesis_prompt: The genre-specific synthesis prompt template.
        writer_level: "elite", "accomplished", or "developing".

    Returns:
        Modified synthesis prompt with calibration block injected.
    """
    config = get_writer_level_config(writer_level)
    calibration_block = config["synthesis_calibration"]

    # Insert calibration before the CRITICAL RULES section
    marker = "CRITICAL RULES FOR THIS REVIEW:"
    if marker in synthesis_prompt:
        return synthesis_prompt.replace(
            marker,
            f"{calibration_block}\n\n{marker}"
        )

    # Fallback: insert before "ORIGINAL ESSAY:" if present
    fallback_marker = "ORIGINAL ESSAY:"
    if fallback_marker in synthesis_prompt:
        return synthesis_prompt.replace(
            fallback_marker,
            f"{calibration_block}\n\n{fallback_marker}"
        )

    # Last resort: append before the end
    return f"{calibration_block}\n\n{synthesis_prompt}"


def build_calibrated_synthesis_prompt(
    synthesis_prompt,
    writer_level,
    is_mixed_genre=False,
    primary_genre=None,
    secondary_genre=None,
    focus=None,
    word_count=None,
):
    """
    Build a synthesis prompt with writer-level calibration and optional
    mixed-genre instructions and focus areas injected.

    Uses the detailed calibration blocks from shared.py (multi-section,
    with separate TONE / OVERALL FEEDBACK / DETAILED COMMENTS / STRENGTHS
    instructions) for maximum impact on synthesis behaviour.

    Injection order before CRITICAL RULES:
        calibration → length calibration → mixed-genre → focus → CRITICAL RULES

    Args:
        synthesis_prompt: The genre's SYNTHESIS_PROMPT template string
        writer_level: "elite", "accomplished", or "developing"
        is_mixed_genre: Whether this is a mixed-genre review
        primary_genre: Primary genre label (required if is_mixed_genre)
        secondary_genre: Secondary genre label (required if is_mixed_genre)
        focus: Optional comma-separated focus areas from the author
        word_count: Optional essay word count for length-adaptive calibration

    Returns:
        Modified synthesis prompt template string (still has {placeholders})
    """
    # Get the detailed calibration block from shared.py
    calibration = CALIBRATION_BLOCKS.get(writer_level, CALIBRATION_BLOCKS["accomplished"]).strip()

    # Build length calibration block if word count available
    length_block = ""
    if word_count is not None:
        length_block = get_length_calibration_block(word_count)

    # Build mixed-genre preamble if needed
    mixed_block = ""
    if is_mixed_genre and primary_genre and secondary_genre:
        mixed_block = MIXED_GENRE_SYNTHESIS_BLOCK.format(
            primary_genre=primary_genre,
            secondary_genre=secondary_genre,
        ).strip()

    # Combine calibration + length + mixed-genre into injection block
    parts = [calibration]
    if length_block:
        parts.append(length_block)
    if mixed_block:
        parts.append(mixed_block)
    injection = "\n\n".join(parts)

    # Add focus block if specified
    if focus and focus.strip():
        focus_block = (
            f"AUTHOR FOCUS AREAS:\n"
            f"The author has asked you to pay particular attention to: {focus.strip()}.\n"
            f"Weight your thematic essays and priority actions accordingly, "
            f"but do not ignore other significant issues."
        )
        injection = f"{injection}\n\n{focus_block}"

    # Insert before CRITICAL RULES (all genres have this marker)
    marker = "CRITICAL RULES FOR THIS REVIEW:"
    if marker in synthesis_prompt:
        return synthesis_prompt.replace(
            marker,
            f"{injection}\n\n{marker}"
        )

    # Fallback: insert before ORIGINAL ESSAY:
    fallback_marker = "ORIGINAL ESSAY:"
    # Also check for ORIGINAL TEXT: (narrative/creative use this)
    if fallback_marker in synthesis_prompt:
        return synthesis_prompt.replace(
            fallback_marker,
            f"{injection}\n\n{fallback_marker}"
        )
    alt_marker = "ORIGINAL TEXT:"
    if alt_marker in synthesis_prompt:
        return synthesis_prompt.replace(
            alt_marker,
            f"{injection}\n\n{alt_marker}"
        )

    # Last resort: prepend
    return f"{injection}\n\n---\n\n{synthesis_prompt}"


# ── v0.9.0: Dynamic criteria support ─────────────────────────────

def should_use_dynamic_criteria(genre_metadata: dict, review_mode: str) -> bool:
    """
    Determine whether to use dynamic criteria generation.

    Returns True when:
    - review_mode is "dynamic" (forced by user)
    - review_mode is "hybrid" (dynamic runs alongside static)
    - Genre is "mixed" (auto-detected as genuinely mixed)
    - Genre confidence is below DYNAMIC_CONFIDENCE_THRESHOLD

    Does NOT return True when:
    - review_mode is "standard" AND genre is confidently classified
    """
    if review_mode == REVIEW_MODE_DYNAMIC:
        return True
    if review_mode == REVIEW_MODE_HYBRID:
        return True

    genre = genre_metadata.get("genre", DEFAULT_GENRE)
    confidence = genre_metadata.get("confidence", 1.0)

    if genre == "mixed":
        return True
    if confidence < DYNAMIC_CONFIDENCE_THRESHOLD:
        return True

    return False


def should_use_static_genre(genre_metadata: dict, review_mode: str) -> bool:
    """
    Determine whether to use static genre dimensions.

    Returns True for standard and hybrid modes when genre is not "mixed".
    In dynamic-only mode, returns False.
    """
    if review_mode == REVIEW_MODE_DYNAMIC:
        return False

    genre = genre_metadata.get("genre", DEFAULT_GENRE)
    confidence = genre_metadata.get("confidence", 1.0)

    # In standard mode, always use static (with fallback to dynamic if needed)
    if review_mode == REVIEW_MODE_STANDARD:
        # Static path unless genre is truly mixed/low-confidence
        if genre == "mixed":
            return False
        if confidence < DYNAMIC_CONFIDENCE_THRESHOLD:
            return False
        return True

    # Hybrid mode: always use static alongside dynamic
    if review_mode == REVIEW_MODE_HYBRID:
        if genre == "mixed":
            # For truly mixed genre, use argumentative as the static baseline
            return True
        return True

    return True


def get_static_genre_for_hybrid(genre_metadata: dict) -> str:
    """
    Determine which static genre to use in hybrid mode.

    For "mixed" genre, falls back to the primary genre or argumentative.
    """
    genre = genre_metadata.get("genre", DEFAULT_GENRE)
    if genre == "mixed" or genre not in SUPPORTED_GENRES:
        # Use the closest static genre — check secondary, then fall back
        secondary = genre_metadata.get("secondary_genre")
        if secondary and secondary in SUPPORTED_GENRES:
            return secondary
        return DEFAULT_GENRE
    return genre


def build_hybrid_synthesis_prompt(
    synthesis_prompt,
    writer_level,
    static_genre,
    focus=None,
    word_count=None,
):
    """
    Build a synthesis prompt for hybrid mode — static genre + dynamic criteria.

    Injects the hybrid preamble, writer-level calibration, and optional focus.
    Uses the DYNAMIC_SYNTHESIS_PROMPT as the base since it's genre-agnostic,
    then adds the hybrid context block.

    Args:
        synthesis_prompt: The base synthesis prompt (dynamic or genre-specific)
        writer_level: "elite", "accomplished", or "developing"
        static_genre: The static genre used for the genre dimension set
        focus: Optional comma-separated focus areas
        word_count: Optional essay word count for length-adaptive calibration

    Returns:
        Modified synthesis prompt template string
    """
    calibration = CALIBRATION_BLOCKS.get(writer_level, CALIBRATION_BLOCKS["accomplished"]).strip()
    hybrid_block = HYBRID_SYNTHESIS_BLOCK.format(genre=static_genre).strip()

    parts = [calibration]
    length_block = ""
    if word_count is not None:
        length_block = get_length_calibration_block(word_count)
    if length_block:
        parts.append(length_block)
    parts.append(hybrid_block)
    injection = "\n\n".join(parts)

    if focus and focus.strip():
        focus_block = (
            f"AUTHOR FOCUS AREAS:\n"
            f"The author has asked you to pay particular attention to: {focus.strip()}.\n"
            f"Weight your thematic essays and priority actions accordingly, "
            f"but do not ignore other significant issues."
        )
        injection = f"{injection}\n\n{focus_block}"

    marker = "CRITICAL RULES FOR THIS REVIEW:"
    if marker in synthesis_prompt:
        return synthesis_prompt.replace(marker, f"{injection}\n\n{marker}")

    alt_marker = "ORIGINAL TEXT:"
    if alt_marker in synthesis_prompt:
        return synthesis_prompt.replace(alt_marker, f"{injection}\n\n{alt_marker}")

    return f"{injection}\n\n---\n\n{synthesis_prompt}"


def build_dynamic_synthesis_with_calibration(
    writer_level,
    focus=None,
    word_count=None,
):
    """
    Build a calibrated dynamic synthesis prompt (no static genre involved).

    Used when the review runs dynamic criteria only (no hybrid).

    Returns:
        Modified DYNAMIC_SYNTHESIS_PROMPT template string
    """
    calibration = CALIBRATION_BLOCKS.get(writer_level, CALIBRATION_BLOCKS["accomplished"]).strip()
    parts = [calibration]

    length_block = ""
    if word_count is not None:
        length_block = get_length_calibration_block(word_count)
    if length_block:
        parts.append(length_block)

    injection = "\n\n".join(parts)

    if focus and focus.strip():
        focus_block = (
            f"AUTHOR FOCUS AREAS:\n"
            f"The author has asked you to pay particular attention to: {focus.strip()}.\n"
            f"Weight your thematic essays and priority actions accordingly, "
            f"but do not ignore other significant issues."
        )
        injection = f"{injection}\n\n{focus_block}"

    marker = "CRITICAL RULES FOR THIS REVIEW:"
    return DYNAMIC_SYNTHESIS_PROMPT.replace(marker, f"{injection}\n\n{marker}")
