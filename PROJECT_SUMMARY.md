# Essay Reviewer — Project Summary (v0.6.0)

## What it does

A Python tool (CLI + web UI) that reviews argumentative and analytical essays using Claude's API. Auto-detects genre, sends the essay through 5 genre-specific parallel analytical dimensions, then synthesises findings into a structured editorial review with thematic essays and surgical detailed comments.

## Architecture

```
cli.py                      → CLI interface (click) with --genre flag
server.py                   → Web server with genre dropdown
ui/
  index.html                → Web interface (dynamic dimension grid)
src/
  orchestrator.py           → Async parallel review + synthesis (genre-aware)
  pipeline.py               → Shared genre-loading utilities
  config.py                 → Genre routing configuration
  genre_detection.py        → Auto-classification prompts + parser
  prompts/
    __init__.py             → Backward-compatible re-exports
    shared.py               → Master system prompt, false-flag filter, shared blocks
    argumentative.py        → 5 argumentative dimensions + synthesis
    analytical.py           → 5 analytical dimensions + synthesis
tests/
  sample_essays/            → Test essay for validation
```

**Pipeline**:
```
Phase 0: Genre Detection (1 API call — or user override)
Phase 1: Parallel Dimension Reviews (5 concurrent API calls, genre-specific)
Phase 2: Synthesis (1 API call, genre-specific prompt + system message)
Phase 3: False-Flag Filter (1 API call, genre-agnostic)
```

Total: 8 API calls. Two independent pipeline implementations: async in orchestrator.py (CLI), synchronous in server.py (web UI).

## Supported Genres

### Argumentative
For thesis-driven essays — politics, policy, opinion, editorial writing.

| Dimension | Focus |
|---|---|
| `conceptual_coherence` | Key term stability, transmission mechanisms, agency, theoretical tensions |
| `argument_architecture` | Thesis precision, continuity vs. rupture, epistemic register, self-undermining logic |
| `evidence_and_claims` | Claim status types, evidential gaps, contested assertions, source quality |
| `precision_and_framing` | Strategic precision, vulnerability to rebuttal, ambiguous comparisons, misattributions |
| `close_reading` | Quote-claim alignment, dangling modifiers, comparison basis, causal overstatement |

### Analytical
For literary criticism, cultural commentary, policy analysis.

| Dimension | Focus |
|---|---|
| `interpretive_depth` | Paraphrase → surface analysis → genuine interpretation hierarchy |
| `evidence_and_textual_support` | Quote selection, integration, commentary, evidence range |
| `framework_and_method` | Theoretical consistency, mechanical vs. responsive application, term stability |
| `balance_and_nuance` | Counter-readings, genuine nuance vs. false balance, limits of interpretation |
| `close_reading_analytical` | Source text accuracy, paraphrase fidelity, quotation accuracy, fair excerpting |

## Output Format

Two sections, calibrated to genre:

1. **Overall Feedback** — 3–8 thematic essays (100–200 words each) addressing cross-cutting issues, plus strengths and priority actions
2. **Detailed Comments** — 4–12 surgical observations with exact quotes

## Shared Capabilities

Written once in `shared.py`, injected into genre prompts at runtime:
- **Register sensitivity** — distinguishes empirical/legal precision from essayistic/rhetorical generalization
- **OCR corruption detection** — garbled transliterations, run-together words, corrupted quotes
- **Endnote/footnote awareness** — reads notes as part of argument

## Usage

```bash
python cli.py setup                              # Configure API key
python cli.py review my_essay.txt                # Auto-detect genre
python cli.py review my_essay.txt --genre analytical  # Force genre
python cli.py review essay.txt -d interpretive_depth -d framework_and_method
python cli.py estimate essay.txt --genre analytical
python cli.py info                               # Show all genres + dimensions
python server.py                                 # Start web UI
```

## Key Design Decisions

- **Quality over quantity**: 5 deep observations beat 50 shallow ones
- **Genre-specific dimensions**: Different writing demands different evaluation criteria
- **Thematic not paragraph-by-paragraph**: Cross-cutting essays, not line-by-line comments
- **Register-aware**: Don't impose academic hedging on essayistic prose
- **No false flags**: Prompts explicitly warn against asserting errors from outdated training data
- **Exact quotes required**: Every detailed comment must anchor to specific text
- **Graceful fallback**: Genre detection defaults to argumentative on any failure

## Dependencies

- Python 3.8+
- anthropic (async + sync clients)
- click (CLI)

## Cost

~£0.15–0.30 per review of a 6,000-word essay using Claude Sonnet 4.
~£1.50–3.00 per review using Claude Opus 4.
