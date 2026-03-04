"""
Genre routing configuration and writer-level calibration.

v0.8.3: Added creative and reflective genres, completing the 6-genre set.
v0.8.2: Added WRITER_LEVEL_CONFIGS for calibrating feedback tone,
comment volume, and synthesis behaviour based on detected writer level.
"""

GENRE_CONFIGS = {
    "argumentative": {
        "module": "src.prompts.argumentative",
        "dimensions": [
            "conceptual_coherence",
            "argument_architecture",
            "evidence_and_claims",
            "precision_and_framing",
            "close_reading",
        ],
        "description": "Essays that advance a thesis and marshal evidence to persuade",
    },
    "analytical": {
        "module": "src.prompts.analytical",
        "dimensions": [
            "interpretive_depth",
            "evidence_and_textual_support",
            "framework_and_method",
            "balance_and_nuance",
            "close_reading_analytical",
        ],
        "description": "Literary criticism, cultural commentary, policy analysis",
    },
    "expository": {
        "module": "src.prompts.expository",
        "dimensions": [
            "clarity_of_explanation",
            "logical_organisation",
            "audience_calibration",
            "evidence_and_examples",
            "completeness_and_gaps",
            "factual_accuracy",
        ],
        "description": "Journalism, reports, explainers, how-to guides, policy briefs",
    },
    "narrative": {
        "module": "src.prompts.narrative",
        "dimensions": [
            "voice_and_tone",
            "structure_and_pacing",
            "scene_and_detail",
            "character_and_perspective",
            "thematic_resonance",
        ],
        "description": "Personal essays, memoir, travel writing, fiction, literary nonfiction",
    },
    "creative": {
        "module": "src.prompts.creative",
        "dimensions": [
            "originality_and_concept",
            "stylistic_coherence",
            "imagery_and_language",
            "formal_risk_and_control",
            "emotional_intellectual_impact",
        ],
        "description": "Fiction, poetry, experimental prose, literary art",
    },
    "reflective": {
        "module": "src.prompts.reflective",
        "dimensions": [
            "self_awareness_and_insight",
            "concrete_grounding",
            "intellectual_integration",
            "growth_and_change",
            "authenticity_and_voice",
        ],
        "description": "Personal reflection, learning journals, meditative essays",
    },
}

DEFAULT_GENRE = "argumentative"
SUPPORTED_GENRES = list(GENRE_CONFIGS.keys())
DEFAULT_WRITER_LEVEL = "accomplished"

# ── v0.9.0: Dynamic criteria configuration ────────────────────

# Genre detection confidence below this triggers the dynamic criteria path
DYNAMIC_CONFIDENCE_THRESHOLD = 0.6

# Review modes
REVIEW_MODE_STANDARD = "standard"   # Static genre dimensions only (default)
REVIEW_MODE_DYNAMIC = "dynamic"     # Dynamic criteria only (forced)
REVIEW_MODE_HYBRID = "hybrid"       # Static genre + dynamic criteria in parallel
SUPPORTED_MODES = [REVIEW_MODE_STANDARD, REVIEW_MODE_DYNAMIC, REVIEW_MODE_HYBRID]


# ── Writer-level calibration ─────────────────────────────────────

WRITER_LEVEL_CONFIGS = {
    "elite": {
        "description": "Published-quality, distinctive voice, sophisticated architecture",
        "tone": "peer-to-peer",
        "comment_guidance": "fewer_high_stakes",
        "max_detailed_comments": 6,
        "synthesis_calibration": (
            "WRITER-LEVEL CALIBRATION — ELITE:\n"
            "This is an accomplished, published-quality piece by an experienced writer. "
            "Your feedback should be architectural and collegial — peer-to-peer, not "
            "teacher-to-student. Focus on the 2-3 most consequential structural or "
            "conceptual issues that even a skilled writer might not see from inside their "
            "own argument. Do NOT flag minor issues that the writer has almost certainly "
            "considered and resolved deliberately. Your Detailed Comments section should "
            "contain ONLY high-stakes observations — issues where the argument's "
            "persuasiveness is materially affected. For an elite writer, 3-6 surgical "
            "comments are more valuable than 12 granular ones. If you find fewer than 3 "
            "issues worth flagging, that is a valid outcome — do not manufacture comments "
            "to fill space."
        ),
    },
    "accomplished": {
        "description": "Competent, well-organised, demonstrates subject knowledge",
        "tone": "constructive",
        "comment_guidance": "standard",
        "max_detailed_comments": 12,
        "synthesis_calibration": (
            "WRITER-LEVEL CALIBRATION — ACCOMPLISHED:\n"
            "This is competent, well-organised writing that demonstrates real subject "
            "knowledge. Your feedback should be substantive and constructive — engaging "
            "seriously with the ideas while offering specific, actionable suggestions. "
            "Both architectural observations and granular comments are appropriate. "
            "Include every observation that meets the quality threshold, whether that's "
            "4 or 12."
        ),
    },
    "developing": {
        "description": "Significant structural, argumentative, or craft weaknesses",
        "tone": "instructional",
        "comment_guidance": "granular",
        "max_detailed_comments": 15,
        "synthesis_calibration": (
            "WRITER-LEVEL CALIBRATION — DEVELOPING:\n"
            "This writing shows areas for significant improvement. Your feedback should "
            "be specific, instructional, and encouraging — help the writer understand not "
            "just WHAT to change but WHY each change matters for their argument. Prioritise "
            "fundamental structural and logical issues over fine-grained observations. "
            "Explain analytical concepts the writer may not be familiar with. Be generous "
            "in the Strengths section — developing writers need to know what they're doing "
            "right as much as what needs work."
        ),
    },
}


def get_genre_config(genre: str) -> dict:
    """Look up configuration for a genre, falling back to default."""
    if genre in GENRE_CONFIGS:
        return GENRE_CONFIGS[genre]
    return GENRE_CONFIGS[DEFAULT_GENRE]


def get_writer_level_config(writer_level: str) -> dict:
    """Look up calibration for a writer level, falling back to accomplished."""
    if writer_level in WRITER_LEVEL_CONFIGS:
        return WRITER_LEVEL_CONFIGS[writer_level]
    return WRITER_LEVEL_CONFIGS["accomplished"]
