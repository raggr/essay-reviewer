#!/usr/bin/env python3
"""
Essay Reviewer — Web Server (v0.9.1: hybrid default + encoding fixes)
Serves the HTML UI and proxies review requests to the Anthropic API.

Usage:
    python server.py                    # starts on port 5000
    python server.py --port 8080        # custom port
"""

import http.server
import json
import os
import sys
import argparse
import webbrowser
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    import anthropic
except ImportError:
    print("Error: 'anthropic' package not installed.")
    print("Run:  pip install anthropic")
    sys.exit(1)

from prompts.shared import MASTER_SYSTEM_PROMPT, FALSE_FLAG_FILTER_PROMPT
from pipeline import (
    load_genre_prompts,
    load_synthesis_system_message,
    build_dimension_system_prompt,
    should_run_mixed_genre,
    load_mixed_genre_prompts,
    build_calibrated_synthesis_prompt,
    should_use_dynamic_criteria,
    should_use_static_genre,
    get_static_genre_for_hybrid,
    build_hybrid_synthesis_prompt,
    build_dynamic_synthesis_with_calibration,
)
from genre_detection import (
    GENRE_DETECTION_SYSTEM,
    GENRE_DETECTION_USER,
    DEFAULT_GENRE_METADATA,
    parse_genre_response,
)
from dynamic_criteria import (
    CRITERIA_GENERATION_SYSTEM,
    CRITERIA_GENERATION_USER,
    DYNAMIC_SYNTHESIS_PROMPT,
    DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE,
    parse_criteria_response,
    criteria_to_dimension_prompts,
)
from config import (
    DEFAULT_GENRE, SUPPORTED_GENRES, DEFAULT_WRITER_LEVEL,
    REVIEW_MODE_STANDARD, REVIEW_MODE_DYNAMIC, REVIEW_MODE_HYBRID,
)
from storage import save_review


def get_api_key():
    """Get API key from environment or .env file"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ANTHROPIC_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
    return api_key


# ── Genre detection (synchronous) ─────────────────────────────────

def detect_genre_sync(client, model, essay_text):
    """
    Classify the essay's genre, secondary genre, and sophistication
    via a synchronous API call.

    Returns:
        Tuple of (genre_metadata dict, tokens_used int)
    """
    try:
        user_prompt = GENRE_DETECTION_USER.format(essay_text=essay_text)

        with client.messages.stream(
            model=model,
            max_tokens=800,  # v0.8.2: increased for additional fields
            temperature=0.1,
            system=GENRE_DETECTION_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            response = stream.get_final_message()

        raw_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        metadata = parse_genre_response(raw_text)
        return metadata, tokens_used

    except Exception as e:
        print(f"Genre detection failed ({e}), falling back to {DEFAULT_GENRE}")
        return dict(DEFAULT_GENRE_METADATA), 0


# ── Dynamic criteria generation (synchronous, v0.9.0) ────────────

def generate_criteria_sync(client, model, essay_text):
    """
    Generate text-specific evaluation criteria via synchronous API call.

    Returns:
        Tuple of (criteria list or None, tokens_used int)
    """
    try:
        user_prompt = CRITERIA_GENERATION_USER.format(essay_text=essay_text)

        with client.messages.stream(
            model=model,
            max_tokens=2000,
            temperature=0.3,
            system=CRITERIA_GENERATION_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            response = stream.get_final_message()

        raw_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        criteria = parse_criteria_response(raw_text)
        return criteria, tokens_used

    except Exception as e:
        print(f"Criteria generation failed: {e}")
        return None, 0


# ── Dimension review ──────────────────────────────────────────────

def run_dimension_review(client, model, dimension_key, dimension_prompts, essay_text, genre_source="", max_tokens=6000):
    """Run a single dimension review (called in thread pool)"""
    dimension = dimension_prompts[dimension_key]
    system_prompt = build_dimension_system_prompt(dimension['prompt'])

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Essay to review:\n\n{essay_text}"}]
    ) as stream:
        response = stream.get_final_message()

    feedback = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return {
        "dimension": dimension['name'],
        "key": dimension_key,
        "feedback": feedback,
        "tokens": tokens,
        "genre_source": genre_source,
    }


# ── Synthesis ─────────────────────────────────────────────────────

def synthesise_reviews(client, model, essay_text, reviews, synthesis_prompt_template, synthesis_system_message, is_mixed=False, max_tokens=16000):
    """Combine dimension reviews into final report using calibrated prompts"""
    # Label reviews by genre source if mixed-genre
    if is_mixed:
        reviews_text = "\n\n".join([
            f"### {r['dimension']} [{r.get('genre_source', '')}]\n{r['feedback']}" for r in reviews
        ])
    else:
        reviews_text = "\n\n".join([
            f"### {r['dimension']}\n{r['feedback']}" for r in reviews
        ])

    prompt = synthesis_prompt_template.format(
        num_reviews=len(reviews),
        essay_text=essay_text,
        reviews=reviews_text
    )

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        system=synthesis_system_message,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        response = stream.get_final_message()

    return response.content[0].text, response.usage.input_tokens + response.usage.output_tokens


# ── False-flag filter ─────────────────────────────────────────────

def filter_false_flags(client, model, report_text, max_tokens=16000):
    """Post-synthesis pass: remove observations based on outdated training knowledge"""
    prompt = FALSE_FLAG_FILTER_PROMPT.format(report=report_text)

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=0.1,
        system="You are a quality-control editor. Your only job is to identify and remove false flags from a draft review — observations where the reviewer flagged something as an error because of outdated training data rather than a genuine problem with the essay. Remove false flags. Keep everything else exactly as-is.",
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        response = stream.get_final_message()

    return response.content[0].text, response.usage.input_tokens + response.usage.output_tokens


# ── Full pipeline ─────────────────────────────────────────────────

def run_full_review(api_key, essay_text, model, dimensions, genre_override=None, focus=None, review_mode=REVIEW_MODE_STANDARD, progress_callback=None):
    """
    Run the full review pipeline:
    genre detection → (optional dynamic criteria) → parallel dimensions → calibrated synthesis → filter

    v0.9.0: Supports three review modes:
    - standard: Static genre dimensions only (default)
    - dynamic: Dynamic text-specific criteria only (forced, or auto when genre confidence is low)
    - hybrid: Static genre + dynamic criteria in parallel
    """
    client = anthropic.Anthropic(api_key=api_key)
    total_tokens = 0

    # ── Phase 0: Genre detection ──────────────────────────────
    if genre_override and genre_override in SUPPORTED_GENRES:
        genre = genre_override
        genre_metadata = dict(DEFAULT_GENRE_METADATA)
        genre_metadata["genre"] = genre
        genre_metadata["confidence"] = 1.0
        if progress_callback:
            progress_callback("genre_detected", f"{genre} (override)")
    else:
        if progress_callback:
            progress_callback("detecting_genre", None)
        genre_metadata, detect_tokens = detect_genre_sync(client, model, essay_text)
        total_tokens += detect_tokens
        genre = genre_metadata.get("genre", DEFAULT_GENRE)
        if genre not in SUPPORTED_GENRES and genre != "mixed":
            genre = DEFAULT_GENRE
        if progress_callback:
            register = genre_metadata.get("register", "unknown")
            writer_level = genre_metadata.get("writer_level", DEFAULT_WRITER_LEVEL)
            secondary = genre_metadata.get("secondary_genre")
            msg = f"{genre} ({register}) · writer: {writer_level}"
            if secondary:
                msg += f" · secondary: {secondary}"
            progress_callback("genre_detected", msg)

    # ── Determine review path ─────────────────────────────────
    sophistication_level = genre_metadata.get("writer_level", DEFAULT_WRITER_LEVEL)
    use_dynamic = should_use_dynamic_criteria(genre_metadata, review_mode)
    use_static = should_use_static_genre(genre_metadata, review_mode)
    is_hybrid = use_dynamic and use_static

    # Determine mixed-genre routing for static path
    is_mixed = (
        use_static
        and not genre_override
        and not is_hybrid  # hybrid replaces mixed-genre routing
        and should_run_mixed_genre(genre_metadata)
    )
    secondary_genre = genre_metadata.get("secondary_genre") if is_mixed else None

    if is_hybrid:
        if progress_callback:
            progress_callback("review_mode", f"Hybrid: static ({genre}) + dynamic criteria")
    elif use_dynamic and not use_static:
        if progress_callback:
            progress_callback("review_mode", "Dynamic: text-specific evaluation criteria")
    elif is_mixed:
        if progress_callback:
            progress_callback("mixed_genre", f"Running {genre} + {secondary_genre} dimensions")

    # ── Phase 0.5 (conditional): Generate dynamic criteria ────
    dynamic_dim_prompts = {}
    generated_criteria = None

    if use_dynamic:
        if progress_callback:
            progress_callback("generating_criteria", None)
        generated_criteria, criteria_tokens = generate_criteria_sync(client, model, essay_text)
        total_tokens += criteria_tokens
        if generated_criteria:
            dynamic_dim_prompts = criteria_to_dimension_prompts(generated_criteria)
            criteria_names = [c["name"] for c in generated_criteria]
            if progress_callback:
                progress_callback("criteria_generated", f"{len(generated_criteria)} criteria: {', '.join(criteria_names)}")
        else:
            if progress_callback:
                progress_callback("criteria_failed", "Falling back to static genre path")
            use_dynamic = False
            use_static = True
            is_hybrid = False

    # ── Load static genre prompts ─────────────────────────────
    primary_dim_prompts = {}
    secondary_dim_prompts = {}
    genre_used = genre

    if use_static:
        static_genre = get_static_genre_for_hybrid(genre_metadata) if is_hybrid else genre
        if static_genre not in SUPPORTED_GENRES:
            static_genre = DEFAULT_GENRE

        if is_mixed:
            mixed = load_mixed_genre_prompts(genre, secondary_genre)
            primary_dim_prompts = mixed["primary_prompts"]
            secondary_dim_prompts = mixed["secondary_prompts"]
            synthesis_prompt_template = mixed["primary_synthesis"]
            synthesis_system_message = mixed["primary_system_message"]
            genre_used = mixed["primary_genre"]
        else:
            primary_dim_prompts, synthesis_prompt_template, genre_used = load_genre_prompts(static_genre)
            synthesis_system_message = load_synthesis_system_message(genre_used)

    # ── Build synthesis prompt ────────────────────────────────
    if is_hybrid:
        calibrated_synthesis = build_hybrid_synthesis_prompt(
            DYNAMIC_SYNTHESIS_PROMPT,
            sophistication_level,
            static_genre=genre_used,
            focus=focus,
        )
        synthesis_system_message = DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE
    elif use_dynamic and not use_static:
        calibrated_synthesis = build_dynamic_synthesis_with_calibration(
            sophistication_level,
            focus=focus,
        )
        synthesis_system_message = DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE
    else:
        calibrated_synthesis = build_calibrated_synthesis_prompt(
            synthesis_prompt_template,
            sophistication_level,
            is_mixed_genre=is_mixed,
            primary_genre=genre_used,
            secondary_genre=secondary_genre,
            focus=focus,
        )

    # ── Phase 1: Parallel dimension reviews ───────────────────
    all_dim_tasks = []

    # Static genre dimensions
    if use_static and primary_dim_prompts:
        if dimensions:
            valid_dims = [d for d in dimensions if d in primary_dim_prompts]
            primary_dim_keys = valid_dims if valid_dims else list(primary_dim_prompts.keys())
        else:
            primary_dim_keys = list(primary_dim_prompts.keys())

        for key in primary_dim_keys:
            all_dim_tasks.append((key, primary_dim_prompts, genre_used))

        # Secondary genre dimensions (mixed-genre only)
        if is_mixed and secondary_dim_prompts:
            for key in list(secondary_dim_prompts.keys()):
                all_dim_tasks.append((key, secondary_dim_prompts, secondary_genre))

    # Dynamic criteria dimensions
    if use_dynamic and dynamic_dim_prompts:
        for key in list(dynamic_dim_prompts.keys()):
            all_dim_tasks.append((key, dynamic_dim_prompts, "dynamic"))

    if not all_dim_tasks:
        raise Exception("No review dimensions could be loaded")

    results = []
    has_mixed_sources = is_mixed or is_hybrid or (use_dynamic and use_static)

    with ThreadPoolExecutor(max_workers=len(all_dim_tasks)) as executor:
        futures = {
            executor.submit(
                run_dimension_review, client, model, key, prompts, essay_text, genre_src
            ): (key, genre_src)
            for key, prompts, genre_src in all_dim_tasks
        }
        for future in as_completed(futures):
            key, genre_src = futures[future]
            try:
                result = future.result()
                results.append(result)
                total_tokens += result['tokens']
                if progress_callback:
                    label = f"{result['dimension']}"
                    if has_mixed_sources:
                        label += f" [{genre_src}]"
                    progress_callback("dimension_done", label)
            except Exception as e:
                if progress_callback:
                    progress_callback("dimension_error", f"{key}: {str(e)}")

    if not results:
        raise Exception("All dimension reviews failed")

    # ── Phase 2: Calibrated synthesis ─────────────────────────
    if progress_callback:
        progress_callback("synthesising", f"writer level: {sophistication_level}")

    synthesis_text, synth_tokens = synthesise_reviews(
        client, model, essay_text, results,
        calibrated_synthesis, synthesis_system_message,
        is_mixed=has_mixed_sources,
    )
    total_tokens += synth_tokens

    # ── Phase 3: False-flag filter ────────────────────────────
    if progress_callback:
        progress_callback("filtering", None)

    filtered_text, filter_tokens = filter_false_flags(client, model, synthesis_text)
    total_tokens += filter_tokens

    # ── Build final report ────────────────────────────────────
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
    word_count = len(essay_text.split())
    dim_names = ', '.join(r['dimension'] for r in results)
    register = genre_metadata.get('register', 'unknown')

    # Determine the review mode actually used
    if is_hybrid:
        mode_used = REVIEW_MODE_HYBRID
    elif use_dynamic and not use_static:
        mode_used = REVIEW_MODE_DYNAMIC
    else:
        mode_used = REVIEW_MODE_STANDARD

    # Build genre line
    confidence = genre_metadata.get('confidence', 0)
    genre_line = f"{genre_used} (register: {register}, confidence: {confidence:.0%})"
    if is_mixed:
        sec_conf = genre_metadata.get('secondary_genre_confidence', 0)
        genre_line += f" + {secondary_genre} (confidence: {sec_conf:.0%}, mixed)"

    focus_line = f"\n**Focus**: {focus}" if focus else ""
    mode_line = f"\n**Mode**: {mode_used}" if mode_used != REVIEW_MODE_HYBRID else ""
    criteria_line = ""
    if generated_criteria:
        criteria_line = f"\n**Dynamic criteria**: {', '.join(c['name'] for c in generated_criteria)}"

    header = f"""# Essay Review

**Date**: {timestamp}
**Word count**: {word_count}
**Model**: {model}
**Genre**: {genre_line}
**Writer level**: {sophistication_level}{mode_line}{focus_line}{criteria_line}
**Dimensions**: {dim_names}
**Total tokens**: {total_tokens:,}

---

"""

    return {
        "report": header + filtered_text,
        "individual_reviews": results,
        "metadata": {
            "word_count": word_count,
            "total_tokens": total_tokens,
            "model": model,
            "dimensions": [r['dimension'] for r in results],
            "timestamp": timestamp,
            "genre": genre_used,
            "genre_metadata": genre_metadata,
            "is_mixed_genre": is_mixed,
            "secondary_genre": secondary_genre,
            "sophistication_level": sophistication_level,
            "writer_level": sophistication_level,
            "focus": focus,
            "review_mode": mode_used,
            "dynamic_criteria": [c["name"] for c in generated_criteria] if generated_criteria else None,
        }
    }


# ── HTTP handler ──────────────────────────────────────────────────

class ReviewHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for the essay reviewer web UI"""

    def __init__(self, *args, api_key=None, **kwargs):
        self.api_key = api_key
        super().__init__(*args, directory=str(Path(__file__).parent / 'ui'), **kwargs)

    def do_POST(self):
        if self.path == '/api/review':
            self._handle_review()
        elif self.path == '/api/validate-key':
            self._handle_validate_key()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        super().do_GET()

    def _handle_validate_key(self):
        """Validate an API key by making a tiny test call"""
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))
        key = body.get('api_key', '').strip()

        if not key:
            self._send_json({"valid": False, "error": "No key provided"})
            return

        try:
            client = anthropic.Anthropic(api_key=key)
            client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            self._send_json({"valid": True})
        except anthropic.AuthenticationError:
            self._send_json({"valid": False, "error": "Invalid API key"})
        except Exception as e:
            self._send_json({"valid": False, "error": str(e)})

    def _handle_review(self):
        """Handle a review request"""
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))

        essay_text = body.get('essay_text', '').strip()
        model = 'claude-sonnet-4-20250514'  # locked: Sonnet only
        dimensions = None  # locked: all dimensions, no client override
        api_key = body.get('api_key', '').strip() or self.server.api_key
        genre_override = None  # locked: always auto-detect
        focus = body.get('focus', None)
        review_mode = REVIEW_MODE_HYBRID  # locked: hybrid only
        consent = bool(body.get('consent', False))  # user opted in to storage

        if not api_key:
            self._send_json({"error": "No API key configured"}, status=401)
            return

        if not essay_text:
            self._send_json({"error": "No essay text provided"}, status=400)
            return

        if len(essay_text.split()) < 50:
            self._send_json({"error": "Essay is too short (minimum ~50 words)"}, status=400)
            return

        try:
            result = run_full_review(api_key, essay_text, model, dimensions, genre_override=genre_override, focus=focus, review_mode=review_mode)
            if consent:
                save_review(essay_text, result)
            self._send_json(result)
        except anthropic.AuthenticationError:
            self._send_json({"error": "Invalid API key"}, status=401)
        except anthropic.RateLimitError:
            self._send_json({"error": "Rate limited — please wait a moment and try again"}, status=429)
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Quieter logging — only show errors and API calls"""
        msg = format % args
        if 'POST' in msg or 'error' in msg.lower() or '404' in msg:
            super().log_message(format, *args)


def make_handler(api_key):
    """Create handler class with api_key bound"""
    def handler(*args, **kwargs):
        return ReviewHandler(*args, api_key=api_key, **kwargs)
    return handler


def main():
    parser = argparse.ArgumentParser(description='Essay Reviewer Web UI')
    parser.add_argument('--port', type=int, default=5000, help='Port (default: 5000)')
    parser.add_argument('--no-browser', action='store_true', help="Don't auto-open browser")
    args = parser.parse_args()

    port = int(os.environ.get('PORT', args.port or 5000))
    host = '0.0.0.0'  # bind to all interfaces for cloud deployment
    api_key = get_api_key()
    ui_dir = Path(__file__).parent / 'ui'
    if not ui_dir.exists() or not (ui_dir / 'index.html').exists():
        print("Error: ui/index.html not found. Make sure the ui/ folder exists.")
        sys.exit(1)

    handler = make_handler(api_key)
    server = http.server.HTTPServer((host, port), handler)
    server.api_key = api_key

    url = f"http://0.0.0.0:{port}"
    print()
    print("╔══════════════════════════════════════════╗")
    print("║       Essay Reviewer  ·  v0.8.2         ║")
    print("╚══════════════════════════════════════════╝")
    print()
    print(f"  Running at:  {url}")
    print(f"  Genres:      {', '.join(SUPPORTED_GENRES)}")
    print(f"  Features:    writer-level calibration, mixed genre handling")
    if api_key:
        print(f"  API key:     ····{api_key[-8:]}")
    else:
        print("  API key:     not set (enter in browser)")
    print()
    print("  Press Ctrl+C to stop")
    print()

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == '__main__':
    main()
