# Essay Reviewer v0.6.0 — Testing Guidance

## Prerequisites

1. Python 3.8+ installed
2. Dependencies: `pip install anthropic click`
3. API key configured in `.env` or environment variable

---

## Test 1: Structural Verification (No API Key Required)

These tests verify that all code loads and connects correctly without making any API calls.

```bash
cd /path/to/essay-reviewer-0.6.0

# 1a. CLI version
python3 cli.py --version
# Expected: cli, version 0.6.0

# 1b. CLI info — should show both genres and all 10 dimensions
python3 cli.py info
# Expected: ARGUMENTATIVE section (5 dims) + ANALYTICAL section (5 dims)

# 1c. CLI help — should show --genre flag
python3 cli.py review --help
# Expected: --genre / -g option with choices: auto, argumentative, analytical

# 1d. Cost estimate (requires API key but no API call for the estimate itself)
python3 cli.py estimate tests/sample_essays/social_media_regulation.txt
python3 cli.py estimate tests/sample_essays/social_media_regulation.txt --genre analytical
# Expected: cost estimates with dimension counts

# 1e. Server starts (Ctrl+C after banner appears)
python3 server.py --no-browser
# Expected: Banner shows "v0.6.0", lists genres: argumentative, analytical
```

---

## Test 2: Web UI Visual Checks (No API Calls)

Start the server and open the browser:

```bash
python3 server.py
```

### 2a. Genre dropdown exists
- [ ] Below the essay text area, there is a "Genre & Review Dimensions" section
- [ ] A dropdown shows: "Auto-detect genre", "Argumentative", "Analytical"

### 2b. Dynamic dimension grid
- [ ] With "Auto-detect genre" selected, 5 argumentative dimensions are shown (all checked)
- [ ] Switch to "Analytical" → grid rebuilds with 5 analytical dimensions:
  - Interpretive Depth
  - Evidence & Textual Support
  - Framework & Method
  - Balance & Nuance
  - Close Reading
- [ ] Switch back to "Argumentative" → grid rebuilds with 5 argumentative dimensions
- [ ] Switch to "Auto-detect genre" → grid shows argumentative dimensions as default
- [ ] All checkboxes work (toggle on/off) after every grid rebuild
- [ ] Cost estimate updates when dimensions are toggled or genre changes

### 2c. File upload still works
- [ ] Drag and drop a `.txt` file → text appears, word count updates
- [ ] Upload a `.docx` file via "Upload file" button → text appears

---

## Test 3: Argumentative Pipeline — CLI (API Calls)

This is the regression test. Output should match v0.5.2 quality.

### 3a. Auto-detect on argumentative text
```bash
python3 cli.py review tests/sample_essays/social_media_regulation.txt
```

**Check:**
- [ ] Genre detection runs ("Detecting genre..." appears)
- [ ] Detected genre is `argumentative`
- [ ] 5 argumentative dimensions run: Conceptual Coherence, Argument Architecture, Evidence & Claims, Precision & Framing, Close Reading
- [ ] Synthesis runs
- [ ] False-flag filter runs
- [ ] Output file created in `output/`
- [ ] Review header shows `Genre: argumentative (register: ...)`
- [ ] Overall Feedback section contains thematic essays (not bullet lists)
- [ ] Detailed Comments have Quote + Feedback format
- [ ] Top 5 Priority Actions listed
- [ ] **No false flags** — no observations based on outdated knowledge

### 3b. Explicit genre override
```bash
python3 cli.py review tests/sample_essays/social_media_regulation.txt --genre argumentative
```

**Check:**
- [ ] "Genre override: argumentative" appears (no detection call)
- [ ] Same dimensions run
- [ ] Output quality equivalent to 3a

---

## Test 4: Analytical Pipeline — CLI (API Calls)

### 4a. Auto-detect on analytical text
```bash
python3 cli.py review tests/sample_essays/ishiguro_unreliable_narrator.txt
```

**Check:**
- [ ] Genre detection runs
- [ ] Detected genre is `analytical` (this essay is literary criticism)
- [ ] 5 analytical dimensions run: Interpretive Depth, Evidence & Textual Support, Framework & Method, Balance & Nuance, Close Reading
- [ ] Review header shows `Genre: analytical (register: ...)`
- [ ] Overall Feedback engages with *interpretive* issues, not argumentative ones:
  - Does it discuss depth of reading vs. surface paraphrase?
  - Does it comment on framework application?
  - Does it assess evidence selection (quoting as argument vs. decoration)?
- [ ] Detailed Comments reference specific passages from the essay
- [ ] **No false flags** — no flagging the Ishiguro analysis as "lacking a thesis" (it's analytical, not argumentative)
- [ ] **Register-appropriate**: doesn't impose argumentative standards on interpretive writing

### 4b. Explicit genre override
```bash
python3 cli.py review tests/sample_essays/ishiguro_unreliable_narrator.txt --genre analytical
```

**Check:**
- [ ] "Genre override: analytical" appears
- [ ] Same dimensions run as 4a

### 4c. Cross-genre test (force wrong genre)
```bash
python3 cli.py review tests/sample_essays/ishiguro_unreliable_narrator.txt --genre argumentative
```

**Check:**
- [ ] Argumentative dimensions run on the analytical text
- [ ] Review still completes without errors
- [ ] Quality will be lower (wrong evaluation criteria) but no crashes

---

## Test 5: Web UI Full Review (API Calls)

### 5a. Auto-detect argumentative
1. Enter API key
2. Paste content of `tests/sample_essays/social_media_regulation.txt`
3. Leave genre on "Auto-detect genre"
4. Leave all dimensions checked
5. Click "Review Essay"

**Check:**
- [ ] Progress shows: Genre detection → 5 dimensions → Synthesis → Quality check
- [ ] All steps complete with ✓
- [ ] Report renders in browser
- [ ] Metadata bar shows: date, word count, model, `argumentative (academic/essayistic/...)`, token count
- [ ] Report quality matches CLI output

### 5b. Force analytical
1. Paste content of `tests/sample_essays/ishiguro_unreliable_narrator.txt`
2. Select "Analytical" from genre dropdown
3. Verify 5 analytical dimensions shown and checked
4. Click "Review Essay"

**Check:**
- [ ] No genre detection step in progress (override)
- [ ] 5 analytical dimensions run
- [ ] Metadata bar shows `analytical (...)`
- [ ] Report engages with interpretive quality, not argumentative structure

### 5c. Auto-detect analytical
1. Paste the Ishiguro essay
2. Select "Auto-detect genre"
3. Click "Review Essay"

**Check:**
- [ ] Genre detection runs
- [ ] Detected as analytical
- [ ] Same quality as 5b

### 5d. Partial dimension selection
1. Paste any essay
2. Select a genre
3. Uncheck some dimensions (leave 2-3 checked)
4. Click "Review Essay"

**Check:**
- [ ] Only selected dimensions run
- [ ] Synthesis still produces a coherent report
- [ ] Cost was lower than all-dimension run

---

## Test 6: Edge Cases

### 6a. Very short text
- Paste fewer than 50 words → server should return error, UI should show it

### 6b. Copy and Download
- [ ] "Copy markdown" button copies raw markdown to clipboard
- [ ] "Download .md" button downloads a file
- [ ] "New review" button clears the form and scrolls to top

### 6c. Model switch
- [ ] Switching to Opus updates cost estimate
- [ ] Review with Opus completes (slower but works)

---

## Test 7: Quality Assessment

These are subjective checks to verify the prompts are producing the right kind of feedback.

### 7a. Argumentative — does the review engage with IDEAS?
Read the review of `social_media_regulation.txt`:
- [ ] Thematic essays address conceptual/structural issues, not just prose style
- [ ] At least one thematic essay identifies a cross-cutting problem (e.g., term instability, self-undermining logic)
- [ ] Detailed comments explain WHY each issue matters for the argument
- [ ] No generic advice ("needs more evidence", "consider the counterargument")
- [ ] Strengths section is specific, not boilerplate

### 7b. Analytical — does the review understand interpretive writing?
Read the review of `ishiguro_unreliable_narrator.txt`:
- [ ] Assesses depth of interpretation (genuine insight vs. surface observation)
- [ ] Evaluates how quotations from the novel are used (argumentative vs. decorative)
- [ ] Comments on framework consistency (formalist reading, narratological approach)
- [ ] Addresses counter-readings or limits of the interpretation
- [ ] Does NOT penalise the essay for lacking a "thesis" in the argumentative sense
- [ ] Does NOT flag rhetorical claims as lacking "evidence"
- [ ] Register sensitivity: treats essayistic generalisations as legitimate craft

### 7c. False-flag check
In BOTH reviews:
- [ ] No observations that flag something as an error based on the reviewer's knowledge being outdated
- [ ] No "temporal confusion" flags (essays written about past events in past tense)
- [ ] No claims that verifiable facts in the essay are wrong (unless they genuinely are)

---

## Test Summary Checklist

```
STRUCTURAL (no API):
[ ] CLI --version shows 0.6.0
[ ] CLI info shows both genres
[ ] CLI review --help shows --genre flag
[ ] Server banner shows v0.6.0 and genre list
[ ] Web UI genre dropdown works
[ ] Web UI dimension grid rebuilds on genre change

CLI REVIEWS (API calls):
[ ] Argumentative auto-detect → correct genre, good output
[ ] Argumentative --genre override → same quality
[ ] Analytical auto-detect → correct genre, good output
[ ] Analytical --genre override → same quality
[ ] Cross-genre (wrong genre forced) → completes without crash

WEB UI REVIEWS (API calls):
[ ] Auto-detect argumentative → correct genre, good report
[ ] Force analytical → analytical dimensions, good report
[ ] Auto-detect analytical → correct genre, good report
[ ] Partial dimension selection → coherent report

QUALITY:
[ ] Argumentative review engages with ideas, not prose style
[ ] Analytical review understands interpretive writing
[ ] No false flags in either pipeline
[ ] Register sensitivity working (no academic hedging on essayistic prose)

EDGE CASES:
[ ] Short text rejected
[ ] Copy/Download/New Review buttons work
[ ] Opus model works (slower)
```

---

## Troubleshooting Test Failures

**Genre detection picks wrong genre**: The detection prompt classifies by structure/rhetoric, not topic. If it misclassifies, the fallback is argumentative, which is safe. Consider using `--genre` override.

**Analytical review imposes argumentative standards**: Check that `REGISTER_SENSITIVITY_BLOCK` is present in the dimension prompt. Run `python3 -c "from src.prompts.analytical import DIMENSION_PROMPTS; print('REGISTER' in DIMENSION_PROMPTS['evidence_and_textual_support']['prompt'])"` — should print `True`.

**False flags appear**: The false-flag filter (Phase 3) should catch these. If one slips through, it means the filter prompt needs strengthening. Note the specific false flag for future improvement.

**Server 500 error**: Check the terminal running `server.py` for the traceback. Most common cause: API key invalid or rate-limited.
