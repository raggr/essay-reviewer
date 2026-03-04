# Essay Reviewer

Deep structural feedback on argumentative and analytical writing, powered by Claude.

Auto-detects your essay's genre, selects the right review dimensions, and produces thematic editorial feedback with surgical detailed comments — comparable to a professional editor.

---

## Step-by-step setup (5 minutes)

### 1. Check you have Python

Open Terminal (Mac) or Command Prompt (Windows) and run:

```
python3 --version
```

You need Python 3.8 or later. If you don't have it, download from https://python.org.

### 2. Unpack and set up the project

Put the `essay-reviewer` folder somewhere sensible (e.g. your home directory, Documents, or Projects).

Then open Terminal, navigate to the folder, and run the setup script:

```
cd /path/to/essay-reviewer
bash setup.sh
```

This does three things: installs Python dependencies, removes macOS Gatekeeper quarantine flags, and makes the start script executable. **You only need to do this once.**

### 3. Get an Anthropic API key

Go to https://console.anthropic.com/ — sign up or log in, then create an API key.

You can either:
- **Option A**: Create a `.env` file in the project folder containing:
  ```
  ANTHROPIC_API_KEY=sk-ant-your-key-here
  ```
- **Option B**: Enter the key in the browser when you start the app (it will save to `.env` for you).

### 4. Start the app

**Double-click** `Start Essay Reviewer.command` in Finder. Your browser opens automatically.

Or from Terminal:
```
python3 server.py
```

Your browser will open automatically to `http://127.0.0.1:5000`. That's it — you're running.

---

## Using the web interface

1. **Enter your API key** (if you didn't create a `.env` file) — it validates automatically and saves for next time.

2. **Paste or upload your essay** — supports `.txt`, `.md`, and `.docx` files. You can also drag and drop.

3. **Choose a genre** — select "Auto-detect" (default), "Argumentative", or "Analytical". Auto-detect analyses your text and picks the right dimension set automatically.

4. **Choose dimensions** — all five are on by default. The dimension grid updates when you change genre. Toggle any off if you want a faster/cheaper review.

5. **Choose a model** — Sonnet 4 is the default (fast, cheap, good). Opus 4 is slower and more expensive but may give deeper insight.

6. **Click "Review Essay"** — takes 1–3 minutes depending on essay length and model.

7. **Read the review** — rendered in the browser with genre and register shown in the metadata bar. You can copy the markdown or download as a `.md` file.

---

## Using the CLI

```
# Review an essay (auto-detects genre)
python3 cli.py review my_essay.txt

# Force a specific genre
python3 cli.py review my_essay.txt --genre analytical
python3 cli.py review my_essay.txt -g argumentative

# Review with specific dimensions only
python3 cli.py review my_essay.txt -d interpretive_depth -d framework_and_method

# Estimate cost before running
python3 cli.py estimate my_essay.txt
python3 cli.py estimate my_essay.txt --genre analytical

# See all genres and dimensions
python3 cli.py info
```

---

## Supported genres

### Argumentative

For essays that advance a thesis and marshal evidence to persuade — politics, policy, opinion, editorial writing.

| Dimension | What it examines |
|---|---|
| **Conceptual Coherence** | Key term stability across contexts, transmission mechanisms, theoretical tensions |
| **Argument Architecture** | Thesis precision, continuity vs. rupture, epistemic register, self-undermining logic |
| **Evidence & Claims** | Claim status types, evidential gaps, contested assertions, source quality |
| **Precision & Framing** | Strategic precision, vulnerability to rebuttal, ambiguous comparisons, misreadings |
| **Close Reading** | Quote-claim alignment, dangling modifiers, comparison basis, causal overstatement |

### Analytical

For literary criticism, cultural commentary, and policy analysis — writing that interprets rather than persuades.

| Dimension | What it examines |
|---|---|
| **Interpretive Depth** | Beyond paraphrase, genuine insight, originality of reading, discovery vs. confirmation |
| **Evidence & Textual Support** | Quote selection and integration, quoting as argument vs. decoration, evidence range |
| **Framework & Method** | Theoretical consistency, mechanical vs. responsive application, term stability |
| **Balance & Nuance** | Counter-readings, genuine nuance vs. false balance, limits of interpretation |
| **Close Reading** | Source text accuracy, paraphrase fidelity, quotation accuracy, fair excerpting |

---

## Output format

The review has two sections:

1. **Overall Feedback** — 3–8 thematic essays (each 100–200 words) addressing cross-cutting structural and conceptual issues, plus strengths and top 5 priority actions.

2. **Detailed Comments** — 4–12 surgical observations about specific passages, each with exact quotes.

Both sections are calibrated to the detected genre. Argumentative reviews focus on logical architecture and evidential rigour; analytical reviews focus on interpretive depth and framework application.

---

## Genre detection

The system automatically classifies your essay by analysing its structure, rhetorical strategy, and relationship to source material — not its topic. An essay about Shakespeare could be argumentative (thesis-driven) or analytical (interpretive), and the system distinguishes between these.

The detected genre and register (academic, essayistic, journalistic, etc.) appear in the review metadata. You can override auto-detection with `--genre` in the CLI or the genre dropdown in the web UI.

---

## Cost

Approximate costs per review of a 6,000-word essay:

| Model | Time | Cost |
|---|---|---|
| Claude Sonnet 4 | ~2–3 min | ~$0.20–0.40 |
| Claude Opus 4 | ~5–10 min | ~$2.00–4.00 |

---

## Project structure

```
essay-reviewer/
├── Start Essay Reviewer.command  ← Double-click to start (Mac)
├── setup.sh            ← Run once: bash setup.sh
├── server.py           ← Web server (genre-aware)
├── cli.py              ← Command-line interface (genre-aware)
├── ui/
│   └── index.html      ← Web interface with genre dropdown
├── src/
│   ├── orchestrator.py ← Async parallel review + synthesis engine
│   ├── pipeline.py     ← Shared genre-loading utilities
│   ├── config.py       ← Genre routing configuration
│   ├── genre_detection.py ← Auto-classification module
│   └── prompts/
│       ├── __init__.py     ← Backward-compatible re-exports
│       ├── shared.py       ← Master system prompt, shared blocks
│       ├── argumentative.py ← 5 argumentative dimensions + synthesis
│       └── analytical.py    ← 5 analytical dimensions + synthesis
├── tests/
│   └── sample_essays/  ← Test essay
├── requirements.txt
├── CHANGELOG.md        ← What changed and why
├── PROJECT_SUMMARY.md  ← Technical overview
└── .env                ← Your API key (created on first use)
```

---

## Troubleshooting

**macOS says "cannot verify" or "malware"** — You haven't run the setup script yet. Open Terminal and run:
```
cd /path/to/essay-reviewer
bash setup.sh
```
This removes Gatekeeper quarantine flags. You only need to do this once.

**"No module named 'anthropic'"** — Run `pip3 install anthropic`

**Port 5000 already in use** — Run `python3 server.py --port 8080`

**API key invalid** — Check for trailing spaces. Key should start with `sk-ant-`.

**Review takes very long** — Opus is slow (5–10 min). Switch to Sonnet for faster results.

**Browser doesn't open** — Navigate manually to `http://127.0.0.1:5000`

---

## Improving the reviewer

To make changes to how the reviewer works, upload this entire project folder to Claude and describe what you want to improve. The prompts in `src/prompts/` are where most of the quality comes from — each genre has its own prompt module. The `CHANGELOG.md` documents the reasoning behind the current design.
