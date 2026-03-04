# CHANGELOG

## v0.9.1 — Minor Fixes + Hybrid Default

**Date**: 2026-03-02

### Summary

Minor release with 4 targeted usability improvements: scripting support, encoding detection, confidence reporting standardization, and hybrid mode as the new default. No prompt or architectural changes.

### Changes

1. **`--yes` / `-y` flag** (cli.py): Skip confirmation prompt for scripted/batch usage
2. **Encoding detection** (cli.py `read_essay()`): Auto-detect and handle Mac Roman, Windows-1252, UTF-8 with BOM, and Latin-1 encoded files
3. **Genre confidence in review headers** (cli.py, server.py): Confidence scores now appear in saved review markdown metadata (previously only in terminal output)
4. **Hybrid mode as default** (cli.py, server.py, ui/index.html): Changed default from `standard` to `hybrid` based on v0.9.0 testing showing consistent value-add across all genres

### Files changed

- `cli.py`: Version bump, `--yes` flag, encoding detection, confidence in headers, hybrid default, mode display logic
- `server.py`: Version bump, confidence in headers, hybrid default
- `ui/index.html`: Hybrid option marked as `selected` by default

### Testing status

- All changes are minor/isolated and preserve backwards compatibility
- Syntax validation passes
- Existing functionality unchanged

---

## v0.9.0 — Dynamic Criteria Generation + Hybrid Mode

**Date**: 2026-03-02

### Summary

Introduces dynamic criteria generation for texts that resist clean genre classification, plus a hybrid review mode that runs static genre dimensions alongside dynamically generated criteria. This is the first major architectural addition since the multi-genre expansion (v0.8.0–v0.8.3).

### New features

- **Dynamic criteria generation** (`src/dynamic_criteria.py`): When genre detection confidence is below 0.6 or genre is classified as "mixed", the system generates 5 evaluation criteria specific to THIS text. Each criterion becomes a dimension prompt that runs in parallel, just like static genre dimensions. Criteria are substantive analytical questions, not thin category labels.

- **Three review modes** (CLI `--mode`, server `mode` field, UI dropdown):
  - `standard` (default): Static genre dimensions only. Unchanged behaviour.
  - `dynamic`: Dynamic text-specific criteria only (forced).
  - `hybrid`: Static genre + dynamic criteria in parallel (doubles dimension count for most comprehensive feedback).

- **Auto-triggering**: In standard mode, the dynamic path auto-triggers when genre confidence < 0.6 or genre is "mixed". No user action needed.

- **Dynamic synthesis prompt**: Genre-agnostic synthesis prompt designed to work with whatever criteria were generated, with full writer-level calibration and focus support.

- **Hybrid synthesis block**: When running hybrid mode, a special preamble instructs the synthesis to draw on both dimension sets, preserve unique observations from each, and produce a unified review.

### Files changed

| File | Change |
|------|--------|
| `src/dynamic_criteria.py` | **NEW** — Criteria generation prompt, dynamic dimension template, dynamic synthesis prompt, hybrid synthesis block, parsing/conversion utilities |
| `src/config.py` | Added `DYNAMIC_CONFIDENCE_THRESHOLD`, review mode constants (`REVIEW_MODE_STANDARD/DYNAMIC/HYBRID`), `SUPPORTED_MODES` |
| `src/pipeline.py` | 5 new functions: `should_use_dynamic_criteria()`, `should_use_static_genre()`, `get_static_genre_for_hybrid()`, `build_hybrid_synthesis_prompt()`, `build_dynamic_synthesis_with_calibration()` |
| `src/orchestrator.py` | Full async support for all three modes: Phase 0.5 (criteria generation), mixed dimension task assembly, mode-aware synthesis routing, updated metadata output |
| `cli.py` | Added `--mode` flag to `review` command. Updated cost estimate, output formatting, and success messages for mode/criteria display |
| `server.py` | Added `generate_criteria_sync()` helper. Updated `run_full_review()` with full dynamic/hybrid support. Updated `_handle_review()` to read `mode` from request body. Updated report header and metadata for mode/criteria |
| `ui/index.html` | Added mode selector dropdown. Updated cost estimate for mode-aware dimension counting. Updated metadata bar to show mode and dynamic criteria (with tooltip) |

### Design decisions

1. **Criteria generation prompt depth**: The prompt explicitly requires specific-to-this-text criteria (not generic rubrics), analytical questions (not checklists), multi-level coverage (conceptual, evidence, technique), and reviewer guidance (what to look for, success vs failure, traps). This prevents the thin-criteria problem.

2. **Dynamic synthesis**: Uses a genre-agnostic prompt with the same quality standards as static synthesis (substance only, internal framing, no false flags, exact quotes, no duplicate actions). Writer-level calibration injected via the same mechanism as static path.

3. **Hybrid synthesis**: The hybrid block instructs synthesis to draw on both static and dynamic dimension sets without separating feedback by source, to deduplicate overlapping observations, and to preserve the strongest unique observation from each dynamic criterion.

4. **Fallback**: If criteria generation fails (API error, malformed JSON), falls back to static genre path silently.

5. **Mixed-genre interaction**: In standard mode, mixed-genre routing and dynamic criteria are alternatives (not combined). In hybrid mode, hybrid replaces mixed-genre routing. The handoff doc's open question about this interaction is resolved by keeping them as separate paths.

### Testing status

- Core module tests pass (imports, routing logic, criteria parsing, dimension generation)
- Syntax validation passes for all changed files
- Requires live API testing with:
  - A clearly classified essay in standard mode (regression test)
  - A genre-bending essay triggering auto-dynamic
  - Forced `--mode dynamic` on a well-classified text
  - `--mode hybrid` on a medium-length essay
  - UI review with mode selector

---

## v0.8.5 — Creative Synthesis Anti-Consistency Rule

**Date**: 2026-03-02

### Summary

Addresses residual micro-level normalisation in creative genre reviews. Testing of v0.8.4's ANTI_NORMALISATION_BLOCK expansion showed macro-level normalisation prevention works but the synthesis prompt still defaults to recommending tonal/stylistic consistency as an improvement — even for writers whose method IS tonal rupture and deliberate inconsistency.

### Change

- **`src/prompts/creative.py`**: Added Rule 10 (`NO CONSISTENCY BIAS`) to creative synthesis CRITICAL RULES. The rule explicitly prohibits recommending consistency as a default improvement, names the specific failure patterns (recommending a text "commit to" a single voice, treating tonal shifts as failures, assuming endings must be "earned"), and requires the reviewer to assess whether inconsistency is the writer's method before treating it as a flaw. Dedup rule renumbered from 10 → 11.

### Root cause analysis

The ANTI_NORMALISATION_BLOCK (in dimension prompts) and STEELMANNING FORMAL CHOICES (synthesis rule 9) prevent the model from normalising "unusual choices" and "formal decisions" — but the model doesn't categorise moment-to-moment tonal shifts as either of these. It sees voice shifts as "inconsistency," a different mental category that neither rule addresses. The new rule directly names the consistency bias as a normalisation pattern.

### Testing status

- Requires re-run of Williams text through creative genre to verify improvement
- All other v0.8.4 tests remain valid (dedup, focus flag, Gaza regression all passed)

---

## v0.8.4 — Prompt Refinements + Register Taxonomy (Bug Fixes)

**Date**: 2026-03-02

### Summary

Fixes bugs and quality issues surfaced during v0.8.3 testing. All changes are prompt-only or detection-prompt updates — no structural/architectural changes.

### Bug fixes

- **Duplicate priority action in reflective synthesis** (Medium): Added `NO DUPLICATE ACTIONS` rule to reflective CRITICAL RULES. The bug caused identical priority actions (#2 and #5) in the dance essay forced-reflective review.
- **Dedup rule audit**: Added `NO DUPLICATE ACTIONS` rule to ALL six genres' synthesis CRITICAL RULES for consistency, not just reflective.

### Quality improvements

- **Anti-normalisation refinement** (creative.py): Strengthened `ANTI_NORMALISATION_BLOCK` with a second paragraph addressing micro-level normalisation. The block now explicitly warns against imposing preferences for formal consistency, integrated symbolism, or earned resolution on writing that deliberately refuses these principles. Also added OCR caveat: anti-normalisation applies to craft choices, not textual corruption.
- **Register taxonomy expansion** (genre_detection.py): Added `children_juvenile` and `popular_commercial` to the register enum. Previously, children's literature was misclassified as "literary" (narrative) or "academic" (creative).

### Files changed

- `src/prompts/creative.py` — ANTI_NORMALISATION_BLOCK expanded (2 new paragraphs), rule 10 added
- `src/prompts/reflective.py` — Rule 10 (NO DUPLICATE ACTIONS) added
- `src/prompts/argumentative.py` — Rule 10 (NO DUPLICATE ACTIONS) added
- `src/prompts/analytical.py` — Rule 10 (NO DUPLICATE ACTIONS) added
- `src/prompts/expository.py` — Rule 12 (NO DUPLICATE ACTIONS) added
- `src/prompts/narrative.py` — Rule 9 (NO DUPLICATE ACTIONS) added
- `src/genre_detection.py` — Register enum expanded, docstring updated
- `cli.py` — Version bumped to 0.8.4
- `server.py` — Version bumped to 0.8.4
- `CHANGELOG.md` — This entry

---

## v0.8.3 — Creative & Reflective Genres + Focus Flag (6-Genre Set Complete)

**Date**: 2026-03-01

### Summary

Completes the 6-genre set by adding creative and reflective writing genres, and introduces the `--focus` flag for author-directed feedback weighting.

### New genres

**Creative** (`src/prompts/creative.py`) — 5 dimensions:
- Originality & Concept, Stylistic Coherence, Imagery & Language, Formal Risk & Control, Emotional & Intellectual Impact
- Includes `ANTI_NORMALISATION_BLOCK` appended to every dimension: assumes unusual choices are deliberate, only flags techniques as problems when the piece's own logic suggests failure
- Shared block injections: `OCR_DETECTION_BLOCK` → imagery_and_language, `REGISTER_SENSITIVITY_BLOCK` → stylistic_coherence

**Reflective** (`src/prompts/reflective.py`) — 5 dimensions:
- Self-Awareness & Insight, Concrete Grounding, Intellectual Integration, Growth & Change, Authenticity & Voice
- Includes `ANTI_PLATITUDE_BLOCK` appended to every dimension: evaluates quality of thinking, not correctness of emotional conclusions
- Shared block injections: `OCR_DETECTION_BLOCK` → concrete_grounding, `REGISTER_SENSITIVITY_BLOCK` → authenticity_and_voice

### Focus flag

- **CLI**: `--focus` / `-f` option (e.g., `--focus "voice,pacing,ending"`)
- **Server**: `focus` field in POST body
- **UI**: Optional "Focus areas" text input below genre selector
- **Pipeline**: Injected into synthesis prompt after calibration block, before CRITICAL RULES
- Focus areas weight thematic essays and priority actions but do not suppress other significant issues

### Infrastructure changes

- **Genre detection** (`genre_detection.py`): Expanded enum to 6 genres. Creative/reflective use elevated mixed-genre threshold (0.65 vs 0.55) to avoid over-triggering.
- **Config** (`config.py`): Two new routing entries with dimension lists and descriptions.
- **Orchestrator** (`orchestrator.py`): Accepts and passes `focus` parameter through pipeline.
- **Pipeline** (`pipeline.py`): `build_calibrated_synthesis_prompt()` accepts `focus` kwarg. Injection order: calibration → mixed-genre → focus → CRITICAL RULES. Added `ORIGINAL TEXT:` as fallback marker for narrative/creative prompts.
- **CLI** (`cli.py`): 6-genre choice list, `--focus` flag, updated info command.
- **Server** (`server.py`): Reads `focus` from POST body, passes through, includes in metadata.
- **UI** (`ui/index.html`): Creative/reflective in dropdown, GENRE_DIMENSIONS entries for both, focus text input, focus displayed in metadata bar.

### Design decisions made

1. Creative/reflective are valid secondary genres for mixed-genre routing, with elevated threshold (0.65)
2. Each genre has its own anti-bias block (ANTI_NORMALISATION_BLOCK for creative, ANTI_PLATITUDE_BLOCK for reflective) kept local to genre files
3. Focus injection order: calibration → mixed-genre → focus → CRITICAL RULES
4. No factual_accuracy dimension for creative (deferred — false-flag filter handles most cases)

---

## v0.8.2 — Detailed Comment Internal Framing + Genre Fallback Fix

**Date**: 2026-03-01

### Problem

v0.8.1 fixed calibration injection and added internal framing to narrative dimension prompts. Testing confirmed that Overall Feedback thematic essays are now internally framed (synthesis Rule 8 works), but Detailed Comments remain externally framed — every comment follows the pattern "More precise phrasing: [rewrite]" without referencing the text's own best moments.

Root cause: the Detailed Comments **Feedback** format line in each genre's synthesis prompt said only `[Your specific observation and suggestion]` without reinforcing the internal framing requirement. The model treats Rule 8 as governing the thematic essays, not the surgical comments.

Additionally, the genre detection prompt offered `reflective`, `creative`, and `mixed` as valid outputs, but none are supported genres — causing silent fallback to `argumentative` and biasing auto-detection away from narrative.

### Changes

**1. Internal framing in detailed comments (4 files)**

Updated the `**Feedback**:` format template in all four genre synthesis prompts to explicitly require internal framing:

- **Argumentative** (`argumentative.py`): "Where possible, ground your suggestion in the essay's own materials — show how an argument, framework, or piece of evidence the essay already deploys elsewhere could resolve this specific issue, rather than prescribing a rewrite from outside."
- **Analytical** (`analytical.py`): "Where possible, ground your suggestion in the text's own readings or evidence — show how an interpretive move or textual observation the analysis already makes elsewhere could resolve this specific issue."
- **Narrative** (`narrative.py`): "Where possible, ground your suggestion in the text's own craft — show how a technique, voice choice, or level of specificity the text already achieves in its strongest passages could resolve this issue."
- **Expository** (`expository.py`): "Where possible, ground your suggestion in the text's own reporting — show how material, structure, or explanatory technique the text already uses elsewhere could resolve this issue."

Also updated the argumentative `INLINE_COMMENT_PROMPT` format.

**2. Genre detection enum narrowing (1 file)**

- `genre_detection.py`: Removed `reflective`, `creative`, and `mixed` from both the detection prompt enum and the `valid_genres` set in `parse_genre_response()`. The model now only outputs the 4 supported genres (`argumentative`, `analytical`, `expository`, `narrative`), eliminating the silent fallback to argumentative.

**3. Mixed-genre synthesis preservation (1 file)**

- `shared.py`: Strengthened `MIXED_GENRE_SYNTHESIS_BLOCK` with two new instructions:
  - "PRESERVE THE STRONGEST UNIQUE OBSERVATIONS from each genre set" — explicitly asks the model to identify the single most valuable unique observation from each secondary-genre dimension before merging
  - "DETAILED COMMENTS should draw from both genre sets" — ensures secondary-genre localised issues aren't lost in synthesis

### Testing

Verify by re-running:
- **Naipaul memoir** (v0.8.2 narrative): Detailed comments should reference the text's own craft rather than prescribing rewrites
- **Gaza essay** (v0.8.2 mixed argumentative+analytical): Detailed comments should reference the essay's own evidence; mixed-genre synthesis should preserve analytical-unique observations (e.g., intention doctrine)
- **Genre detection**: Run a reflective/creative text and confirm it maps to narrative, not argumentative

---

## v0.8.1 — Calibration Pipeline Fix + Narrative Internal Framing

**Date**: 2026-03-01

### What broke in v0.8.0

Writer-level calibration never reached the synthesis prompt due to three interlocking bugs:

1. **Function name mismatch**: `server.py` imported `build_calibrated_synthesis_prompt` but `pipeline.py` only defined `inject_calibration_into_synthesis`. The calibration function existed but was never called.
2. **Field name mismatch**: `server.py` read `sophistication_level` from genre metadata, but genre detection returns `writer_level`. The level was always `None`, defaulting to "accomplished" regardless of detection.
3. **Missing orchestrator**: `src/orchestrator.py` was absent from the source tree — only stale `.pyc` bytecode existed. The CLI ran from cached bytecode that predated the calibration changes.
4. **Dict key mismatch**: `server.py` referenced `primary_dimensions` / `primary_synthesis_prompt` from `load_mixed_genre_prompts()`, but the function returns `primary_prompts` / `primary_synthesis`.

Net effect: every v0.8.0 review ran with no calibration block in the synthesis prompt, producing identical output to v0.7.5.

### Fixes

**Calibration pipeline (5 files)**:
- `src/pipeline.py`: Added `build_calibrated_synthesis_prompt()` as a proper export using detailed multi-section calibration blocks from `shared.py`. Re-exports `should_run_mixed_genre` from `genre_detection.py`.
- `src/config.py`: Added `DEFAULT_WRITER_LEVEL = "accomplished"` constant.
- `server.py`: Fixed field names (`writer_level` not `sophistication_level`), fixed mixed-genre dict keys, added `writer_level` to metadata return.
- `src/orchestrator.py`: Recreated from scratch with correct imports and field names.
- `ui/index.html`: Fixed to check both `writer_level` and `sophistication_level` fields.

**Narrative internal framing (1 file)**:
- `src/prompts/narrative.py`: Added craft-internal suggestion framing to 4 of 5 dimension prompts (`voice_and_tone`, `structure_and_pacing`, `scene_and_detail`, `character_and_perspective`). `thematic_resonance` already had it from v0.7.5.

### Testing

All 8 integration tests pass: full import chain, genre detection field names, mixed genre routing, calibration injection (4 genres × 3 levels), mixed genre + calibration, narrative internal framing (5/5), detection prompt fields, DEFAULT_WRITER_LEVEL constant.

### Verification plan

Re-run Naipaul memoir through v0.8.1. Expected: `Writer level: elite` in header, 3–6 detailed comments (was 10), peer-to-peer tone, internally framed suggestions.

---

## v0.8.0 — Writer-Level Calibration + Mixed Genre Handling

### What changed and why

v0.7.5's refine.ink comparison revealed two major gaps: (1) refine.ink performs explicit writer-level assessment before generating feedback — calibrating tone, depth, and comment volume for the specific writer, while our system treats student essays and Coates identically; (2) the Coates essay demonstrated that some texts are genuinely both argumentative and narrative, but our system forces a single genre classification, missing complementary insights.

v0.8.0 addresses both gaps with infrastructure changes that affect every review, not just edge cases.

### Changes made

#### 1. Enhanced genre detection (Phase 0)

The genre detection prompt now returns three additional signals in a single API call (no additional API cost):

- **`secondary_genre`** + **`secondary_confidence`**: Identifies whether the text blends genres (e.g., argumentative + narrative), with a confidence score and rationale.
- **`sophistication_level`**: Classifies writer command as `elite`, `accomplished`, or `developing` based on observable craft features (sentence complexity, structural choices, evidence handling, rhetorical range).
- **`sophistication_signals`**: Brief justification of the level assessment.

The `parse_genre_response()` function validates all new fields with sensible fallbacks: unknown sophistication levels default to `accomplished`, redundant secondary genres (secondary == primary) are rejected, unsupported secondary genres are nullified.

#### 2. Mixed genre routing

When genre detection returns a `secondary_genre` with confidence ≥ 0.4 (`MIXED_GENRE_THRESHOLD` in config.py), the pipeline runs dimension reviews from BOTH genres in parallel. For a text that is both argumentative and narrative, this means 10 dimensions instead of 5 — but the complementary insights (argument structure from the argumentative lens, craft quality from the narrative lens) are non-overlapping.

Implementation:
- `pipeline.py`: `should_run_mixed_genre()` checks threshold; `load_mixed_genre_prompts()` loads both dimension sets
- `orchestrator.py` / `server.py`: All dimension tasks (primary + secondary) are dispatched concurrently; results are labelled with `genre_source` so synthesis knows which lens each observation came from
- `shared.py`: `MIXED_GENRE_SYNTHESIS_BLOCK` instructs the synthesis model to unify observations from both genres without duplicating or separating by genre

Cost implication: Mixed-genre reviews cost ~2x for the dimension phase. For a 5,000-word essay at Sonnet pricing, this is ~$0.80-$1.00 vs ~$0.40-$0.50 for single-genre. Genre override (`--genre argumentative`) bypasses mixed-genre routing entirely.

#### 3. Writer-level calibration

The synthesis prompt is dynamically modified based on the detected sophistication level. Three calibration blocks in `shared.py` adjust:

**Elite** (peer-to-peer):
- Architectural feedback only — skip issues a writer at this level would self-correct
- High bar for detailed comments: 3-6 high-impact comments, zero is acceptable
- Collegial tone: "One structural move worth considering..." not "You should..."

**Accomplished** (standard editorial):
- Full range of architectural and conceptual feedback
- Standard substance threshold: 4-12 detailed comments
- Constructive expert tone

**Developing** (instructional):
- Foundational issues first (thesis clarity, evidence deployment, structural coherence)
- More granular comments with explanations of underlying principles: 8-15 typical
- Supportive mentoring tone: "The reason this matters is..."

The calibration block is injected BEFORE the genre's base synthesis prompt via `build_calibrated_synthesis_prompt()`, so the model reads calibration instructions first and applies them to all subsequent rules.

#### 4. Pipeline architecture

No new API calls added. The calibration and mixed-genre decisions are folded into existing pipeline phases:
- Phase 0: Returns enhanced metadata (same 1 API call, slightly higher `max_tokens`)
- Phase 1: Runs 5-10 dimensions in parallel (10 only if mixed-genre triggered)
- Phase 2: Synthesis receives calibrated prompt (same 1 API call)
- Phase 3: False-flag filter unchanged

### Files changed

- `src/genre_detection.py` — Enhanced prompt + validation for secondary genre, sophistication level
- `src/config.py` — `MIXED_GENRE_THRESHOLD`, `WRITER_LEVELS`, `get_writer_level_config()`
- `src/pipeline.py` — `should_run_mixed_genre()`, `load_mixed_genre_prompts()`, `get_calibration_block()`, `build_calibrated_synthesis_prompt()`
- `src/prompts/shared.py` — `CALIBRATION_BLOCK_ELITE/ACCOMPLISHED/DEVELOPING`, `MIXED_GENRE_SYNTHESIS_BLOCK`
- `src/orchestrator.py` — Mixed-genre dimension dispatch, calibrated synthesis, `genre_source` on ReviewResult
- `server.py` — Same changes as orchestrator (sync version), version bump to v0.8.0
- `cli.py` — Version bump, writer level + mixed genre in output metadata
- `ui/index.html` — Writer level badge + mixed genre label in metadata bar
- `CHANGELOG.md` — This entry

### Design decisions

1. **Single API call for all Phase 0 signals.** Adding a separate writer-calibration step would add latency and cost. The genre detection prompt is already reading the full essay; asking it to also assess sophistication is a natural extension of the same cognitive task.

2. **Calibration block BEFORE synthesis prompt.** The calibration instructions must be the first thing the model reads, because they modify how all subsequent rules are interpreted (e.g., "apply a HIGH BAR for detailed comments" changes the meaning of "include every observation that meets this threshold").

3. **Mixed genre threshold at 0.4.** Conservative enough to avoid false mixed-genre triggering (most single-genre texts will get 0.0-0.2 secondary confidence), permissive enough to catch genuine blends like the Coates essay. Adjustable in `config.py`.

4. **Primary genre synthesis prompt as base.** For mixed-genre reviews, the primary genre's synthesis prompt is used as the base (with the mixed-genre block prepended). This avoids the complexity of merging two different synthesis prompts, and the primary genre is the more dominant voice.

5. **No dimension-level calibration.** The calibration only affects synthesis, not the individual dimension reviews. Dimension prompts should always produce their best observations regardless of writer level — the synthesis phase is where gating and tone adjustment happen.

### Testing plan

1. **Coates ("My President Was Black") — auto-detect**: Should trigger mixed-genre routing (argumentative + narrative). Should detect writer level as `elite`. Synthesis should produce architectural feedback with minimal detailed comments.
2. **Kesavan (Islamicate cinema)**: Should detect as `analytical`, likely `elite` or `accomplished`. No mixed-genre routing expected. Confirm no regression.
3. **London Bridge (journalism)**: Should detect as `expository`, likely `accomplished`. Confirm no regression on factual catches.
4. **Short student essay** (if available): Should detect as `developing`. Confirm more granular, instructional feedback with higher comment count.
5. **Genre override test**: `--genre argumentative` should bypass both mixed-genre routing and auto-detection.

---

## v0.7.5 — Argument-Internal Framing & Steelmanning (All Genres)

### What changed and why

Analysis of refine.ink's leaked `<skill>` tag on the Coates review revealed a key quality distinction: refine.ink consistently frames suggestions in terms of the essay's own materials ("the essay's own examples — birtherism, voting restrictions, the badge of whiteness — to demonstrate exactly what the economic alternative cannot explain"), while our reviews often frame them externally ("the essay must clarify X"). This is the difference between collaborative refinement (showing the author what their materials can already do) and external evaluation (telling the author what's wrong).

Our synthesis prompts already had rules 8 (argument-internal framing) and 9 (steelmanning) — but the Coates argumentative review didn't follow them. Root cause: the dimension prompts that generate the raw observations had bare "Suggest how to resolve it" instructions with no internal-framing guidance. The model generates externally-framed observations at the dimension level, and the synthesis inherits them. Both levels must align.

### Changes made

#### 1. Dimension-level internal framing (8 dimensions across 4 genres)

Added internal-framing guidance to suggestion instructions:

**Argumentative** (3 dimensions): `conceptual_coherence` ("show how existing evidence in other sections can be redeployed"), `argument_architecture` ("show the author that their own building blocks can be rearranged"), `evidence_and_claims` ("show how evidence the essay ALREADY deploys elsewhere could close this gap")

**Analytical** (2 dimensions): `framework_and_method` ("show how the text's own close readings already contain the materials"), `balance_and_nuance` (added steelmanning: "show how the text's own evidence could steelman the alternative")

**Expository** (2 dimensions): `clarity_of_explanation` ("show how the text's own material elsewhere already contains the explanation"), `completeness_and_gaps` ("show how the text's own reporting already contains material to address the gap")

**Narrative** (1 dimension): `thematic_resonance` ("show how the text's own strongest moments already achieve the resonance that weaker passages reach for")

#### 2. Synthesis-level concrete before/after examples (all 4 genres)

Added concrete EXTERNAL (weak) vs INTERNAL (strong) examples to synthesis rules:

**Argumentative** rules 8 + 9:
- Rule 8: "The essay must clarify whether Obama was strategically accommodating or genuinely naive" → "Section II's insight that Obama's accommodation was 'demonstrably necessary as a matter of political survival' already contains the framework to resolve this apparent contradiction..."
- Rule 9: "The essay should engage more seriously with economic explanations" → "The strongest version of the economic argument would note... The essay's own evidence — birtherism, voter restrictions — demonstrates precisely what this steelmanned economic account cannot explain..."

**Analytical** rules 8 + 9: Genre-adapted examples using close reading / framework tensions.

**Expository** rules 10 + 11 (new): Explanation-internal framing + steelmanning for balanced exposition.

**Narrative** rule 8 (new): Craft-internal framing showing how the text's strongest moments set a standard.

### Architectural principle

Internal framing must be established at BOTH levels: dimension prompts (where raw observations are generated) AND synthesis prompts (where they're composed into the final review). If dimension prompts generate externally-framed observations, the synthesis will reproduce that framing even with explicit instructions to do otherwise.

### Source: refine.ink leaked `<skill>` block

The Coates review leaked refine.ink's internal reasoning process:
- Writer-level calibration ("high-level, elite writer" → "collegial, peer-to-peer" → "collaborative refinement")
- Argument-internal framing ("where the essay's own evidence can be deployed more effectively")
- Steelmanning as specific recommendation
- Comment-level gating (zero detailed comments for an elite writer)

v0.7.5 implements argument-internal framing and steelmanning. Writer-level calibration and comment-level gating are scoped for v0.8.0.

### Files changed

- `src/prompts/argumentative.py` — 3 dimension suggestions + synthesis rules 8-9 with before/after examples
- `src/prompts/analytical.py` — 2 dimension suggestions + synthesis rules 8-9 with before/after examples
- `src/prompts/expository.py` — 2 dimension suggestions + synthesis rules 10-11 with examples
- `src/prompts/narrative.py` — 1 dimension suggestion + synthesis rule 8 with example
- `cli.py` — version bump
- `server.py` — version bump
- `CHANGELOG.md` — this entry

### Testing plan

1. **Coates argumentative re-run**: Look for "Section II already contains..." style framing. Steelmanning should appear for economic-vs-racial explanation.
2. **London Bridge expository**: Suggestions should point to the text's own materials.
3. **Regression**: Confirm no degradation.

---

## v0.7.4 — Dedicated Factual Accuracy Dimension for Expository + Block Redistribution

### What changed and why

v0.7.3 added factual verification, sourcing standards, and contingency language as appended blocks on existing expository dimensions. Testing against the London Bridge essay showed **zero improvement** — 0/8 factual catches again, identical to v0.7.2. The sourcing and contingency blocks also produced no observations.

Root cause: **prompt overload and cognitive mode mismatch.** The `evidence_and_examples` dimension went from ~6,200 chars to ~10,800 chars with four stacked blocks (OCR + endnotes + factual verification + sourcing). The model prioritised the core prompt's evidence-evaluation task and treated the appended fact-checking blocks as supplementary. More fundamentally, fact-checking (pausing on each claim to query training knowledge) is a different cognitive operation from evidence evaluation (assessing whether examples illuminate). Stacking both on one dimension meant neither got full attention.

The fix: **promote factual verification to a dedicated 6th dimension** with its own API call, so the model enters fact-checking mode from the first word. Redistribute the other blocks to dimensions where they fit naturally.

### Changes made

#### 1. New dedicated dimension: `factual_accuracy` (expository)

A full ~4,000-char prompt focused entirely on claim verification. The prompt:
- Opens by setting the cognitive mode: "You are a fact-checker, not an editor"
- Specifies the method: "Read sentence by sentence. For each specific factual claim, pause and ask: Is this correct?"
- Provides 8 categories of factual error with worked examples drawn from the London Bridge failures:
  1. Wrong titles/roles/official styles (Camilla: Princess Consort vs Duchess of Cornwall)
  2. Wrong person/wrong event (Bishop of London vs Bishop of Lincoln)
  3. Wrong material/description (chestnut vs oak roof — explicitly named as known case)
  4. Anachronistic terminology ("feudal" for Anglo-Saxon assemblies)
  5. Chronological conflation (Bagehot 1867 vs Empress of India 1876)
  6. Category errors (non-realm ≠ republic)
  7. Mischaracterised origins ("revived" vs originated)
  8. Ambiguous factual phrasing (misleading even if technically defensible)
- Maintains false-flag caution: "If you find no errors, say so. Do not manufacture issues."

This adds one API call per expository review (~$0.05-0.10 on Sonnet).

#### 2. Block redistribution

| Block | v0.7.3 location | v0.7.4 location | Rationale |
|---|---|---|---|
| `FACTUAL_VERIFICATION_BLOCK` | evidence_and_examples | **removed** (superseded by dedicated dimension) | Dedicated dimension does the job better |
| `SOURCING_STANDARDS_BLOCK` | evidence_and_examples | **completeness_and_gaps** | Sourcing gaps are a kind of incompleteness; this dimension already looks for what's missing |
| `CONTINGENCY_LANGUAGE_BLOCK` | clarity_of_explanation | **audience_calibration** | Treating plans as certainties is a register/calibration issue, not an explanation-clarity issue |
| `OCR_DETECTION_BLOCK` | evidence_and_examples | evidence_and_examples (unchanged) | Still appropriate here |
| `ENDNOTE_AWARENESS_BLOCK` | evidence_and_examples | evidence_and_examples (unchanged) | Still appropriate here |

`evidence_and_examples` drops from ~10,800 chars back to ~6,300 chars — restored to its original focused job.

#### 3. Synthesis updated

Expository synthesis prompt now references "factual accuracy" alongside other dimensions in its scope.

### Architectural principle established

**Appended blocks work for detection/filter tasks** (OCR corruption, structural repetition, register sensitivity) that operate as checks on the model's existing analytical process. They **fail for tasks requiring a different cognitive mode** (systematic factual verification, sourcing assessment). Tasks requiring the model to read in a fundamentally different way need their own dimension with a dedicated API call.

### Block injection table (complete, all genres)

| Dimension | REG | OCR | END | DOM | S_REP | FACT | SRC | CONT | WKSHP |
|---|---|---|---|---|---|---|---|---|---|
| **Argumentative** | | | | | | | | | |
| conceptual_coherence | — | — | — | — | — | — | — | — | — |
| argument_architecture | — | — | — | — | — | — | — | — | — |
| evidence_and_claims | — | — | — | — | — | — | — | — | — |
| precision_and_framing | — | — | — | — | — | — | — | — | — |
| close_reading | ✓ | ✓ | — | ✓ | ✓ | — | — | — | — |
| **Analytical** | | | | | | | | | |
| interpretive_depth | — | — | — | — | — | — | — | — | — |
| evidence_and_textual_support | ✓ | — | ✓ | — | — | — | — | — | — |
| framework_and_method | — | — | — | — | — | — | — | — | — |
| balance_and_nuance | ✓ | — | ✓ | — | ✓ | — | — | — | — |
| close_reading_analytical | — | ✓ | — | ✓ | ✓ | — | — | — | — |
| **Expository** | | | | | | | | | |
| clarity_of_explanation | — | — | — | — | — | — | — | — | — |
| logical_organisation | — | — | — | — | ✓ | — | — | — | — |
| audience_calibration | ✓ | — | — | — | — | — | — | **✓** | — |
| evidence_and_examples | — | ✓ | ✓ | — | — | — | — | — | — |
| completeness_and_gaps | — | — | — | — | — | — | **✓** | — | — |
| **factual_accuracy** | — | — | — | — | — | **DEDICATED** | — | — | — |
| **Narrative** | | | | | | | | | |
| voice_and_tone | — | — | — | — | — | — | — | — | ✓ |
| structure_and_pacing | — | — | — | — | ✓ | — | — | — | ✓ |
| scene_and_detail | — | — | — | — | — | — | — | — | ✓ |
| character_and_perspective | — | ✓ | — | — | — | — | — | — | ✓ |
| thematic_resonance | — | — | — | — | — | — | — | — | ✓ |

### Files changed

- `src/prompts/expository.py` — new `factual_accuracy` dimension; blocks redistributed; synthesis updated
- `src/config.py` — expository now has 6 dimensions
- `ui/index.html` — factual_accuracy added to expository dimension grid
- `cli.py` — version bump
- `server.py` — version bump
- `CHANGELOG.md` — this entry

### Files unchanged

- `src/prompts/shared.py` — no changes (blocks still defined there, just redistributed)
- `src/prompts/argumentative.py` — no changes (register fix from v0.7.3 retained)
- `src/prompts/analytical.py` — no changes
- `src/prompts/narrative.py` — no changes
- All infrastructure files — no changes

### Cost implication

Expository reviews now use 6 parallel dimension calls instead of 5, adding ~$0.05-0.10 per review on Sonnet. Total expository review cost: ~$0.40-0.75 (from ~$0.35-0.65).

### Testing target

London Bridge re-run: **≥4/8 factual catches** (chestnut/oak, Camilla's title, wrong bishop, "36 republics" are all well within training data). Sourcing should appear from `completeness_and_gaps`. Contingency from `audience_calibration`. No regression on comprehension/structure observations.

---

## v0.7.3 — Expository Factual Verification, Sourcing Standards, Contingency Language + Argumentative Register Fix

### What changed and why

v0.7.2 was tested with two essays: Sam Knight's "London Bridge is Down" (expository/journalistic) and Ta-Nehisi Coates's "My President Was Black" (auto-detected argumentative/literary; also run manually as narrative).

The London Bridge test exposed a critical gap: refine.ink caught **8 specific factual errors** (wrong bishop, wrong roof material, anachronistic terminology, incorrect title, etc.) while our review caught **zero**. The expository prompts had no factual verification capability — they evaluated comprehension, structure, and audience calibration but never checked whether claims were true. For journalism, factual accuracy is the highest-stakes dimension.

refine.ink also identified three journalism-specific concerns absent from our prompts: sourcing tier distinctions (documented vs. briefed vs. inferred), contingency language (treating plans and projections as certainties with "will"), and the establishment-viewpoint framing.

The Coates test exposed a residual register sensitivity gap: two detailed comments in the argumentative review were hedging-requests that should have been filtered (suggesting "laws would have barred his parents' marriage" to replace Coates's rhetorical "laws barring his very conception"; suggesting "need little interpretation" overstates the case for an FBI death threat). Root cause: `REGISTER_SENSITIVITY_BLOCK` was not injected into argumentative `close_reading`.

### Changes made

#### 1. Factual verification block (NEW — `shared.py`)

New `FACTUAL_VERIFICATION_BLOCK` targeting verifiable claims in journalism and reportage. Different from `DOMAIN_VERIFICATION_BLOCK` (which targets obscure texts and traditions in analytical/argumentative writing). This block targets seven categories:

1. **Institutional facts**: titles, roles, official styles (e.g., "Princess Consort" vs "Duchess of Cornwall")
2. **Historical claims**: specific events, participants, dates (e.g., which bishop died at a funeral)
3. **Physical/architectural claims**: materials, measurements, descriptions of well-known structures (e.g., oak vs chestnut roof)
4. **Chronological consistency**: temporal relationships between events, people, and concepts (e.g., Bagehot 1867 vs "Empress of India" 1876)
5. **Terminological precision**: specialist terms used correctly (e.g., "feudal" for pre-Conquest Anglo-Saxon assemblies)
6. **Category errors**: conflation of related but distinct categories (e.g., non-realm Commonwealth members ≠ "republics")
7. **Ceremonial/procedural origins**: "revived" vs "originated" for traditions

Injected into: expository `evidence_and_examples`.

#### 2. Sourcing standards block (NEW — `shared.py`)

New `SOURCING_STANDARDS_BLOCK` for journalism-specific sourcing awareness. Distinguishes four tiers: documented sources → first-hand accounts → institutional knowledge → inference/projection. Flags when high-impact claims rest on weak sourcing tiers, when the text shifts tiers without signalling, or when anonymous attribution is used for contested analysis rather than operational details.

Injected into: expository `evidence_and_examples`.

#### 3. Contingency language block (NEW — `shared.py`)

New `CONTINGENCY_LANGUAGE_BLOCK` targeting the "will" problem — where texts about plans and protocols present contingent events with unconditional certainty. Distinguishes constitutional necessities (must happen by law) from operational plans (planned but subject to change) from projections (author's predictions). Flags when genuinely uncertain projections carry the same declarative force as documented plans.

Injected into: expository `clarity_of_explanation`.

#### 4. Register sensitivity added to argumentative close_reading

`REGISTER_SENSITIVITY_BLOCK` was missing from argumentative `close_reading` — the dimension that produced both hedging-request comments in the Coates review. Now injected, bringing it into parity with how other genres handle register.

#### 5. Expository synthesis prompt updated

Added rules 8 (factual claims matter most) and 9 (sourcing and contingency) to the synthesis critical rules, ensuring the synthesis pass prioritises factual catches and sourcing distinctions.

### Block injection table (complete, all genres)

| Dimension | REGISTER | OCR | ENDNOTE | DOMAIN | STRUCT_REP | FACTUAL | SOURCING | CONTINGENCY | WORKSHOP |
|---|---|---|---|---|---|---|---|---|---|
| **Argumentative** | | | | | | | | | |
| conceptual_coherence | — | — | — | — | — | — | — | — | — |
| argument_architecture | — | — | — | — | — | — | — | — | — |
| evidence_and_claims | — | — | — | — | — | — | — | — | — |
| precision_and_framing | — | — | — | — | — | — | — | — | — |
| close_reading | **✓ NEW** | ✓ | — | ✓ | ✓ | — | — | — | — |
| **Analytical** | | | | | | | | | |
| interpretive_depth | — | — | — | — | — | — | — | — | — |
| evidence_and_textual_support | ✓ | — | ✓ | — | — | — | — | — | — |
| framework_and_method | — | — | — | — | — | — | — | — | — |
| balance_and_nuance | ✓ | — | ✓ | — | ✓ | — | — | — | — |
| close_reading_analytical | — | ✓ | — | ✓ | ✓ | — | — | — | — |
| **Expository** | | | | | | | | | |
| clarity_of_explanation | — | — | — | — | — | — | — | **✓ NEW** | — |
| logical_organisation | — | — | — | — | ✓ | — | — | — | — |
| audience_calibration | ✓ | — | — | — | — | — | — | — | — |
| evidence_and_examples | — | ✓ | ✓ | — | — | **✓ NEW** | **✓ NEW** | — | — |
| completeness_and_gaps | — | — | — | — | — | — | — | — | — |
| **Narrative** | | | | | | | | | |
| voice_and_tone | — | — | — | — | — | — | — | — | ✓ |
| structure_and_pacing | — | — | — | — | ✓ | — | — | — | ✓ |
| scene_and_detail | — | — | — | — | — | — | — | — | ✓ |
| character_and_perspective | — | ✓ | — | — | — | — | — | — | ✓ |
| thematic_resonance | — | — | — | — | — | — | — | — | ✓ |

### Files changed

- `src/prompts/shared.py` — three new blocks (FACTUAL_VERIFICATION, SOURCING_STANDARDS, CONTINGENCY_LANGUAGE)
- `src/prompts/expository.py` — new imports; blocks injected into clarity_of_explanation and evidence_and_examples; synthesis rules 8-9 added
- `src/prompts/argumentative.py` — REGISTER_SENSITIVITY_BLOCK imported and injected into close_reading
- `cli.py` — version bump
- `server.py` — version bump
- `CHANGELOG.md` — this entry

### Files unchanged

- `src/prompts/analytical.py`, `src/prompts/narrative.py` — no changes
- All infrastructure files — no changes

### Test results driving these changes

#### London Bridge v0.7.2 (expository) vs refine.ink

| refine.ink catch | Our v0.7.2 | Category |
|---|---|---|
| Camilla's title (Princess Consort vs Duchess of Cornwall) | missed | Institutional fact |
| "36 republics" (non-realm ≠ republic) | missed | Category error |
| "Anglo-Saxon feudal assembly" (anachronistic) | missed | Terminological precision |
| Bishop of London died (wrong bishop) | missed | Historical claim |
| Bagehot/Empress of India chronological conflation | missed | Chronological consistency |
| "Revived" Vigil of Princes (originated, not revived) | missed | Ceremonial origins |
| "National anthem on drums" (ambiguous phrasing) | missed | Factual precision |
| "Chestnut roof" (oak, not chestnut) | missed | Physical/architectural |
| Sourcing tier distinctions | missed | Journalism-specific |
| Contingency vs certainty ("will" language) | missed | Journalism-specific |
| Establishment viewpoint framing | missed | Journalism-specific |

0/8 factual catches, 0/3 journalism-specific catches = critical gap.

#### Coates v0.7.2 (argumentative) register issues

| Comment | Problem | Root cause |
|---|---|---|
| "Laws barring his very conception" → suggested more precise version | Hedging request on rhetorical claim | REGISTER block missing from close_reading |
| "Need little interpretation" → suggested overstatement | Hedging request on obvious reading | REGISTER block missing from close_reading |

### Testing plan for v0.7.3

1. **London Bridge re-run** (PRIMARY): Target ≥4/8 factual catches. Sourcing and contingency observations should appear in thematic essays. No regression on comprehension/structure observations.
2. **Coates argumentative re-run**: Two hedging comments should be eliminated. No regression on thematic observations.
3. **Kesavan/Roy regression**: Confirm no degradation on analytical essays.

---

## v0.7.2 — Expository & Narrative Genres

### What changed and why

v0.7.1 completed the prompt refinement cycle for the two existing genres (argumentative and analytical). With register sensitivity, OCR detection, endnote awareness, domain verification, and structural repetition all working, the prompt infrastructure is mature enough to support new genres without quality regression on existing ones.

v0.7.2 adds two new genres — expository and narrative — covering the majority of humanities writing. Expository handles journalism, reports, explainers, how-to guides, and policy briefs. Narrative handles personal essays, memoir, travel writing, fiction, and literary nonfiction.

### Changes made

#### 1. Expository genre (`src/prompts/expository.py`)

Five new dimension prompts calibrated for explanatory writing:

| Dimension | What it examines |
|---|---|
| `clarity_of_explanation` | Conceptual sequence, assumed knowledge gaps, premature abstraction, explanation vs. assertion, metaphor failure |
| `logical_organisation` | Section ordering, transition quality, promise fulfilment, parallelism, redundancy. Includes `STRUCTURAL_REPETITION_BLOCK`. |
| `audience_calibration` | Over/under-explanation, register consistency, jargon handling, expertise signalling. Includes `REGISTER_SENSITIVITY_BLOCK`. |
| `evidence_and_examples` | Claim-evidence relationships, example quality and integration, factual accuracy. Includes `OCR_DETECTION_BLOCK` and `ENDNOTE_AWARENESS_BLOCK`. |
| `completeness_and_gaps` | Title-content alignment, framing-body alignment, perspective balance, unmet promises |

Synthesis prompt framed around reader comprehension: "how well the text teaches, explains, and orients its reader."

#### 2. Narrative genre (`src/prompts/narrative.py`)

Five new dimension prompts calibrated for narrative craft:

| Dimension | What it examines |
|---|---|
| `voice_and_tone` | Distinctiveness, sustainability, tonal control, unreliable narration as deliberate technique |
| `structure_and_pacing` | Emotional/thematic logic, longueurs, non-linear structure, earned endings. Includes `STRUCTURAL_REPETITION_BLOCK`. |
| `scene_and_detail` | Specific vs. generic detail, fresh vs. received imagery, functional detail, earned lyricism, when telling is right |
| `character_and_perspective` | Specificity vs. type, interiority, point of view, self-awareness in memoir. Includes `OCR_DETECTION_BLOCK`. |
| `thematic_resonance` | Earned vs. asserted meaning, through-line beyond chronology, subtext, proportionality of ending |

**Workshop-boilerplate prevention.** Every narrative dimension prompt includes an `ANTI_WORKSHOP_BLOCK` that explicitly bans generic workshop advice: "show don't tell," "avoid adverbs," "use active voice," "the opening should hook the reader," "make the character more likeable." The model is instructed that these are surface-level prescriptions that ignore context and that its job is to assess whether THIS text's craft choices serve THIS text's goals.

Synthesis prompt framed around craft: "someone who has read deeply in the genre, respects the writer's ambitions, and can articulate precisely where the text succeeds and where it falls short on its own terms."

#### 3. Infrastructure updates

- `src/config.py` — added expository and narrative genre configs
- `ui/index.html` — added genre dropdown options and dimension grid data for both genres
- `cli.py` — updated description for 4-genre support; genre choices auto-populate from config

**No pipeline changes needed.** The genre detection, routing, and synthesis infrastructure built in v0.6.0 handled the expansion without modification. `pipeline.py`, `orchestrator.py`, `server.py`, and `genre_detection.py` all work with the new genres out of the box.

#### 4. Shared capability injection

Both new genres use shared blocks from `shared.py`:

| Dimension | REGISTER | OCR | ENDNOTE | STRUCT_REP | WORKSHOP |
|---|---|---|---|---|---|
| **Expository** | | | | | |
| clarity_of_explanation | — | — | — | — | — |
| logical_organisation | — | — | — | ✓ | — |
| audience_calibration | ✓ | — | — | — | — |
| evidence_and_examples | — | ✓ | ✓ | — | — |
| completeness_and_gaps | — | — | — | — | — |
| **Narrative** | | | | | |
| voice_and_tone | — | — | — | — | ✓ |
| structure_and_pacing | — | — | — | ✓ | ✓ |
| scene_and_detail | — | — | — | — | ✓ |
| character_and_perspective | — | ✓ | — | — | ✓ |
| thematic_resonance | — | — | — | — | ✓ |

### Files changed

- `src/prompts/expository.py` — NEW: 5 dimension prompts + synthesis prompt + system message
- `src/prompts/narrative.py` — NEW: 5 dimension prompts + synthesis prompt + system message
- `src/config.py` — added expository and narrative genre configs
- `ui/index.html` — genre dropdown options + dimension data for both genres
- `cli.py` — version bump + updated description
- `server.py` — version bump
- `CHANGELOG.md` — this entry

### What did NOT change

- `src/prompts/shared.py` — no changes (shared blocks already sufficient)
- `src/prompts/argumentative.py` — no changes
- `src/prompts/analytical.py` — no changes
- `src/pipeline.py` — no changes (dynamic loading already works)
- `src/orchestrator.py` — no changes
- `server.py` — no changes beyond version bump
- `src/genre_detection.py` — no changes (already recognises all genres)

### Testing plan

1. **Expository**: Run against a long-form journalism piece, a policy explainer, and a how-to guide. Verify feedback focuses on comprehension, not thesis strength. Confirm genre detection routes correctly.
2. **Narrative**: Run against a personal essay, a piece of memoir, and a short story. Verify zero generic workshop advice. Confirm deliberate craft choices are not flagged as errors.
3. **Regression**: Re-run Kesavan and Roy essays to confirm no degradation.
4. **Genre detection**: Verify correct classification across at least 8 texts spanning all 4 genres.

---

## v0.7.1 — Prompt Fixes: Domain Verification, Structural Repetition, OCR Precision

### What changed and why

v0.7.0 was tested against the Kesavan and Roy essays with Sonnet. Results: register sensitivity and OCR detection improved dramatically (Kesavan: 3/4 OCR catches, 0 hedging comments, endnote tension caught). However, the Roy essay exposed persistent gaps: all four domain-specific catches that refine.ink made were still missed (Tuhfat/akhlaq conflation, Upanishads/rajadharma misattribution, sati vs widow remarriage, structural loop in conclusion). Additionally, one review produced a false positive — flagging a legitimate transliteration variant ("Tuhfat-ul-Muwahhidin") as OCR corruption.

v0.7.1 addresses these specific failures through targeted prompt strengthening.

### Changes made

#### 1. Domain verification made active with worked examples

The `DOMAIN_VERIFICATION_BLOCK` was rewritten from passive ("flag with confidence when...") to active ("this is a required step — actively verify every claim"). Key additions:

- Worked example for text mischaracterisation: theological/rationalist tract vs. *akhlaq* political philosophy — explains the genre distinction concretely
- Worked example for wrong source tradition: Upanishads (metaphysical) vs. epic/*dharmaśāstra* (kingship ethics) — names the correct traditions
- Worked example for conflated movements: anti-*sati* activism (Roy, widow immolation) vs. widow remarriage (Vidyasagar, a generation later) — names the leaders, periods, and the distinction
- These same worked examples propagated into both genre close_reading prompts

#### 2. Structural repetition detection added

New `STRUCTURAL_REPETITION_BLOCK` in `shared.py` detects passages that cover the same ground twice with overlapping diction — specifically the "double conclusion" pattern where an essay begins to conclude, steps back into summary, then concludes again. Integrated into:
- `close_reading_analytical` as item 10
- `close_reading` (argumentative) as item 9
- Appended to `balance_and_nuance` analytical dimension

#### 3. OCR scanning strengthened with verse-by-verse instruction

Added explicit instruction to read EVERY quoted verse, lyric fragment, or transliterated passage individually and sound each word out. This targets the missed "Mujhko shah bhar baithna" corruption. The instruction appears in both the shared `OCR_DETECTION_BLOCK` and both close_reading dimension prompts.

#### 4. OCR false-positive guardrail added

Added explicit instruction: "Do NOT flag established transliteration variants as OCR corruption. For example, 'ul' vs 'al' in Arabic-derived terms reflects different romanisation conventions, not corruption." This addresses the false positive on "Tuhfat-ul-Muwahhidin" in the Roy review.

### Files changed

- `src/prompts/shared.py` — strengthened domain block, new structural repetition block, OCR verse scanning + false-positive guardrail
- `src/prompts/analytical.py` — integrated all changes into close_reading_analytical (items 8-10) and balance_and_nuance
- `src/prompts/argumentative.py` — integrated all changes into close_reading (items 7-9)
- `cli.py` — version bump to 0.7.1
- `server.py` — version bump to 0.7.1
- `CHANGELOG.md` — this entry

### Test results driving these changes

#### Kesavan v0.7.0 Sonnet (strong — minor fix needed)

| Check | v0.6.0 | v0.7.0 | Target |
|---|---|---|---|
| Register hedging | 6 comments | 0 | ✅ Fixed |
| OCR: "Peno-Arabic" | missed | caught | ✅ |
| OCR: "kiagni" | missed | caught | ✅ |
| OCR: "Thibo Babu" | missed | caught | ✅ |
| OCR: "Mujhko shah bhar" | missed | **missed** | v0.7.1 fix |
| Endnote tension | missed | caught | ✅ |

#### Roy v0.7.0 Sonnet (domain gaps remain)

| Check | v0.7.0 | refine.ink | Target |
|---|---|---|---|
| Register hedging | 0 | 0 | ✅ |
| Tuhfat/akhlaq conflation | missed | caught | v0.7.1 fix |
| Upanishads/rajadharma | missed | caught | v0.7.1 fix |
| Sati vs widow remarriage | missed | caught | v0.7.1 fix |
| Structural loop | missed | caught | v0.7.1 fix |
| Transliteration false positive | flagged wrongly | — | v0.7.1 fix |

---

## v0.7.0 — Prompt Refinement: Register, OCR, Endnotes, Domain

### What changed and why

v0.6.0 testing against refine.ink benchmarks revealed four systematic quality gaps: the system produced hedging comments on essayistic prose (register insensitivity), missed every instance of textual corruption in scanned/OCR'd texts, failed to cross-reference endnotes against main-text claims, and missed domain-specific misattributions that professional reviewers caught. v0.7.0 is a prompt-only release that closes these gaps — no infrastructure, UI, or pipeline changes.

### Changes made

#### 1. Strengthened register sensitivity (high impact)

The register instructions in `MASTER_SYSTEM_PROMPT`, `REGISTER_SENSITIVITY_BLOCK`, both synthesis prompts, and `FALSE_FLAG_FILTER_PROMPT` have been substantially rewritten. Key changes:

- Added concrete examples of what NOT to flag: "'X is the language men die in' is a rhetorical gesture — do NOT suggest 'X provides the dominant lexicon for...'"
- Introduced the "FIRST CHECK" principle: before writing any overstatement comment, ask whether the suggested revision makes the essay better or worse. This test now takes priority over any instinct to qualify.
- Explicitly distinguished type (a) empirical assertions from type (b) rhetorical crystallisations — only type (a) should be flagged.
- Added register-aware filtering to `FALSE_FLAG_FILTER_PROMPT` so hedging comments that slip through dimension reviews are caught at the filter stage.
- Added register awareness rule to both genre synthesis prompts.

#### 2. Strengthened OCR / textual corruption detection (high impact)

The `OCR_DETECTION_BLOCK` has been rewritten from a passive instruction into an explicit, numbered task with concrete examples. Key changes:

- Promoted from appended afterthought to integrated core task (items 8/7 in close_reading dimensions) with "DEDICATED SCAN" framing — the model is told this is a separate task it must not skip.
- Added concrete examples: "Peno-Arabic" for "Perso-Arabic", "kiagni" for "ki agni", "Thibo Babu" for George Thibaut.
- Added footnote/endnote priority: "OCR corruption is most common in footnotes, endnotes, transliterated text, and quoted verse. Scan these sections with particular care."
- Added unidentifiable reference flagging even when the reviewer is unsure of the correct identification.

#### 3. Strengthened endnote awareness (medium impact)

The `ENDNOTE_AWARENESS_BLOCK` and the MASTER_SYSTEM_PROMPT endnote section now specify two concrete patterns:

- Main-text vs. notes tension: confident structural claim in main text + qualifying evidence in footnote = structural tension to flag.
- Buried evidence: crucial qualifications in notes not integrated into the main argument.
- Added instruction to cross-reference each major claim against footnotes/endnotes.
- Added `ENDNOTE_AWARENESS_BLOCK` to the `balance_and_nuance` analytical dimension.

#### 4. Added domain knowledge verification (medium impact, cautious)

New `DOMAIN_VERIFICATION_BLOCK` added to `shared.py` and integrated into both genres' close_reading dimensions. This captures low-hanging domain catches without creating a hallucination trap:

- High-confidence flags: text mischaracterisation (theological tract described as political philosophy), conflation of distinct reform movements (sati vs. widow remarriage), ideas attributed to wrong genre of text within a tradition.
- Question-framed flags: suspected but uncertain misattributions framed as questions, not corrections.
- Explicit restraint: "Do NOT guess about obscure texts" and "a false correction is far worse than a missed one."

### Files changed

- `src/prompts/shared.py` — strengthened all four capability blocks + false-flag filter
- `src/prompts/analytical.py` — integrated OCR + domain into close_reading body, added endnote block to balance_and_nuance, register rule in synthesis
- `src/prompts/argumentative.py` — strengthened OCR + added domain in close_reading, register rule in synthesis
- `cli.py` — version bump to 0.7.0
- `server.py` — version bump to 0.7.0
- `CHANGELOG.md` — this entry

### What did NOT change

- No infrastructure, pipeline, UI, or CLI changes
- No new genres or dimensions
- No token limit or temperature changes
- No model-level fixes

---

## v0.6.0 — Multi-Genre Support (Argumentative + Analytical)

### What changed and why

v0.5.2 was locked to argumentative writing — it had one set of review dimensions and one synthesis prompt, both calibrated for thesis-driven essays. This works well for politics, policy, and editorial writing, but produces awkward results when applied to literary criticism, cultural commentary, or interpretive analysis. A dimension called "Evidence & Claims" that asks whether the essay "distinguishes moral certainty from judicial findings" is the wrong question for a reading of Middlemarch.

v0.6.0 adds a second genre (analytical) with its own dimension set, synthesis prompt, and evaluation criteria, plus the infrastructure to add more genres in future releases.

### Changes made

#### 1. Multi-genre pipeline architecture

The pipeline now has four phases:

1. **Phase 0: Genre Detection** — a lightweight API call classifies the essay's genre (argumentative or analytical) and register (academic, essayistic, journalistic, etc.) by analysing structure and rhetorical strategy, not topic. Falls back to argumentative on any failure.
2. **Phase 1: Parallel Dimension Reviews** — 5 concurrent API calls using genre-specific dimensions.
3. **Phase 2: Synthesis** — genre-specific synthesis prompt and system message.
4. **Phase 3: False-Flag Filter** — unchanged, genre-agnostic.

Both the async pipeline (orchestrator.py / CLI) and the synchronous pipeline (server.py / web UI) are fully genre-aware.

#### 2. Prompts restructured as package

`src/prompts.py` replaced by `src/prompts/` package:
- `shared.py` — master system prompt, false-flag filter, and shared capability blocks (register sensitivity, OCR detection, endnote awareness)
- `argumentative.py` — 5 argumentative dimensions + synthesis prompt + system message
- `analytical.py` — 5 analytical dimensions + synthesis prompt + system message
- `__init__.py` — backward-compatible re-exports so existing code doesn't break

#### 3. New analytical dimensions

| Dimension | What it examines |
|---|---|
| `interpretive_depth` | Paraphrase → surface analysis → genuine interpretation hierarchy |
| `evidence_and_textual_support` | Quoting as decoration vs. quoting as argument |
| `framework_and_method` | Mechanical vs. responsive framework application |
| `balance_and_nuance` | Genuine nuance vs. false balance; counter-readings |
| `close_reading_analytical` | Source text misreadings, paraphrase fidelity, quotation accuracy |

Each prompt is 400–600 words of specific analytical intelligence, not a thin rubric.

#### 4. Register sensitivity

The master system prompt now distinguishes between:
- **Empirical/legal/policy writing** — precision is paramount, hedging is expected
- **Essayistic/cultural-critical/polemical writing** — rhetorical generalization is legitimate craft

A litmus test is embedded: "Would your revision make the essay BETTER or WORSE?" This prevents the reviewer from imposing academic hedging on essayistic prose or flagging rhetorical conviction as evidential overreach.

#### 5. OCR corruption detection

The close reading dimensions now include a textual integrity check: garbled transliterations, run-together words, corrupted quotations, and unidentifiable references that may indicate OCR artefacts in scanned source texts.

#### 6. Endnote/footnote awareness

The master system prompt now instructs the reviewer to read endnotes and footnotes as part of the argument, and to flag where notes undermine the main text without acknowledgment.

#### 7. Genre-aware CLI

- `--genre` flag on `review` command: `auto` (default), `argumentative`, `analytical`
- `info` command shows both genre dimension sets
- `estimate` command accepts `--genre`
- Review output header includes detected genre and register

#### 8. Genre-aware web UI

- Genre dropdown: Auto-detect / Argumentative / Analytical
- Dimensions grid rebuilds dynamically when genre changes
- API request passes genre (null for auto-detect)
- Metadata bar shows detected genre and register
- Cost estimate includes genre detection call

#### 9. New modules

- `src/pipeline.py` — shared utilities for loading genre prompts dynamically
- `src/config.py` — genre routing configuration
- `src/genre_detection.py` — classification prompts and response parser

---

## v0.2.0 — Quality Overhaul

### What changed and why

These improvements were made after comparing the essay reviewer's output against a professional editorial review (refine.ink) of the same essay. The comparison revealed that our reviewer was producing high-volume, low-depth feedback — 67 shallow paragraph-by-paragraph notes where the professional service produced 5 deep thematic essays and 4 surgical comments that were far more useful.

### The core problem

Our reviewer was behaving like a rubric-checking teaching assistant. The professional review behaved like a knowledgeable colleague who had read the essay carefully, understood its ambition, and could articulate exactly where the conceptual architecture failed to support that ambition.

### Changes made

1. **Completely rewritten `MASTER_SYSTEM_PROMPT`** — from "expert editor and writing coach" to "senior academic editor and intellectual peer reviewer". Added explicit instruction to engage with IDEAS, warning against false flags, ban on generic advice, instruction to identify the essay's central ambition.

2. **Restructured review dimensions (4 → 4, fundamentally different)** — from checklist-style (thesis? logical fallacies? self-contradiction? jargon?) to depth-oriented (self-undermining logic, epistemic registers, concept stability, strategic precision).

3. **New `conceptual_coherence` dimension** — examines key term stability, transmission mechanisms, agency attribution, and contradictory theoretical commitments. This was the single most valuable insight from the refine.ink comparison.

4. **Completely rewritten `SYNTHESIS_PROMPT`** — from paragraph-by-paragraph inline comments to two distinct sections: thematic essays (3-6, each 100-200 words) and surgical detailed comments (4-8 with exact quotes).

5. **Output format matches professional standard** — structured detailed comments with Status, Quote, and Feedback fields.

6. **Synthesis temperature lowered (0.5 → 0.3)** — more precise analytical prose.

7. **Synthesis token limit increased (8000 → 12000)** — substantive thematic essays need more space.
