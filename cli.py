#!/usr/bin/env python3
"""
Command-line interface for essay reviewer (v0.9.1)
"""

import asyncio
import click
import os
from pathlib import Path
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from orchestrator import EssayReviewer
from config import (
    GENRE_CONFIGS, SUPPORTED_GENRES, DEFAULT_GENRE,
    SUPPORTED_MODES, REVIEW_MODE_STANDARD, REVIEW_MODE_DYNAMIC, REVIEW_MODE_HYBRID,
)
from pipeline import load_genre_prompts


def get_api_key():
    """Get API key from environment or .env file"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not found in environment or .env file", err=True)
        click.echo("Create a .env file with: ANTHROPIC_API_KEY=your_key_here", err=True)
        sys.exit(1)

    return api_key


def read_essay(file_path: str) -> str:
    """Read essay text from file, handling common encodings."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Essay file not found: {file_path}")

    raw = path.read_bytes()

    # Try UTF-8 first (most common)
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        pass

    # Try UTF-8 with BOM
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        pass

    # Fall back to Windows-1252 (superset of Mac Roman for most text)
    try:
        text = raw.decode('windows-1252')
        click.echo(f"   ⚠️  File encoding: Windows-1252/Mac Roman (converted to UTF-8)")
        return text
    except UnicodeDecodeError:
        pass

    # Last resort: latin-1 (never fails, but may garble some characters)
    text = raw.decode('latin-1')
    click.echo(f"   ⚠️  File encoding: unknown (decoded as Latin-1)")
    return text


def save_review(review_text: str, output_path: str):
    """Save review to file"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(review_text)


# Build the list of all valid dimension keys across all genres
ALL_DIMENSION_KEYS = []
for cfg in GENRE_CONFIGS.values():
    for d in cfg["dimensions"]:
        if d not in ALL_DIMENSION_KEYS:
            ALL_DIMENSION_KEYS.append(d)


@click.group()
@click.version_option(version='0.9.1')
def cli():
    """
    AI-powered essay reviewer for argumentative, analytical, expository,
    narrative, creative, and reflective writing.

    Provides deep, substantive feedback on politics, culture, literary criticism,
    journalism, memoir, fiction, poetry, and more. Auto-detects genre or accepts
    --genre override. Supports --focus to weight feedback toward specific areas.
    """
    pass


@cli.command()
@click.argument('essay_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Output file path (default: auto-generated in ./output/)')
@click.option('--dimensions', '-d', multiple=True,
              type=click.Choice(ALL_DIMENSION_KEYS),
              help='Specific dimensions to review (default: all for detected genre)')
@click.option('--genre', '-g',
              type=click.Choice(['auto'] + SUPPORTED_GENRES),
              default='auto',
              help='Essay genre: auto-detect or one of the 6 supported genres (default: auto)')
@click.option('--mode', '-m',
              type=click.Choice(SUPPORTED_MODES),
              default=REVIEW_MODE_HYBRID,
              help='Review mode: standard (static genre dims), dynamic (text-specific criteria), '
                   'hybrid (both in parallel, default). Use --mode standard for static-only reviews.')
@click.option('--focus', '-f', default=None,
              help='Comma-separated focus areas (e.g., "voice,pacing,ending")')
@click.option('--model', default='claude-sonnet-4-20250514',
              help='Claude model to use')
@click.option('--yes', '-y', is_flag=True, default=False,
              help='Skip confirmation prompt (for scripted/batch usage)')
def review(essay_file, output, dimensions, genre, mode, focus, model, yes):
    """
    Review an essay and generate comprehensive feedback.

    Examples:
        python cli.py review my_essay.txt
        python cli.py review my_essay.txt --genre analytical
        python cli.py review my_essay.txt --genre creative --focus "imagery,ending"
        python cli.py review my_essay.txt --mode hybrid
        python cli.py review my_essay.txt --mode dynamic
        python cli.py review my_essay.txt -g argumentative -o review_output.md
        python cli.py review my_essay.txt -d conceptual_coherence -d argument_architecture
    """
    try:
        # Load essay
        click.echo(f"📄 Loading essay from {essay_file}...")
        essay_text = read_essay(essay_file)
        word_count = len(essay_text.split())
        click.echo(f"   Word count: {word_count}")

        # Genre
        genre_override = genre if genre != 'auto' else None
        if genre_override:
            click.echo(f"   Genre: {genre_override} (override)")
        else:
            click.echo(f"   Genre: auto-detect")
        if mode != REVIEW_MODE_HYBRID:
            click.echo(f"   Mode: {mode}")
        if focus:
            click.echo(f"   Focus: {focus}")

        # Get API key
        api_key = get_api_key()

        # Initialize reviewer
        reviewer = EssayReviewer(
            api_key=api_key, model=model,
            genre_override=genre_override, review_mode=mode,
        )

        # Show cost estimate
        dims_to_run = list(dimensions) if dimensions else None
        num_dims = len(dimensions) if dimensions else 5
        cost_estimate = reviewer.estimate_cost(word_count, num_dims, review_mode=mode)
        click.echo(f"\n💰 Estimated cost: £{cost_estimate['cost_gbp']} "
                   f"(${cost_estimate['cost_usd']})")
        click.echo(f"   Tokens: ~{cost_estimate['estimated_input_tokens'] + cost_estimate['estimated_output_tokens']:,}")
        if mode == REVIEW_MODE_HYBRID:
            click.echo(f"   ⚠️  Hybrid mode runs ~10 dimensions (higher cost)")

        # Confirm
        if not yes and not click.confirm('\n🚀 Proceed with review?', default=True):
            click.echo("Review cancelled.")
            return

        # Run review
        click.echo(f"\n🤖 Running review ({mode} mode) with {num_dims}+ dimensions...")
        click.echo("   This will take 1-3 minutes...\n")

        result = asyncio.run(reviewer.review_essay(
            essay_text,
            dimensions=dims_to_run,
            focus=focus,
        ))

        # Determine output path
        if not output:
            output_dir = Path(__file__).parent / 'output'
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            essay_name = Path(essay_file).stem
            output = output_dir / f"{essay_name}_review_{timestamp}.md"

        # Format and save review
        review_content = result['summary_and_inline']

        # Add metadata header
        metadata = result['metadata']
        genre_used = metadata.get('genre', 'unknown')
        genre_meta = metadata.get('genre_metadata', {})
        register = genre_meta.get('register', 'unknown')
        confidence = genre_meta.get('confidence', 0)
        sophistication = metadata.get('writer_level', 'accomplished')
        is_mixed = metadata.get('is_mixed_genre', False)
        secondary = metadata.get('secondary_genre')
        review_mode_used = metadata.get('review_mode', REVIEW_MODE_STANDARD)
        dynamic_criteria = metadata.get('dynamic_criteria')

        genre_line = f"{genre_used} (register: {register}, confidence: {confidence:.0%})"
        if is_mixed and secondary:
            sec_conf = genre_meta.get('secondary_genre_confidence', 0)
            genre_line += f" + {secondary} (confidence: {sec_conf:.0%}, mixed)"

        focus_line = metadata.get('focus', '')
        mode_line = review_mode_used
        if dynamic_criteria:
            mode_line += f" — criteria: {', '.join(dynamic_criteria)}"

        header = f"""# {Path(essay_file).stem.replace('_', ' ').title()} — Review

**Date**: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}  
**Essay**: {Path(essay_file).name}  
**Word count**: {metadata['word_count']}  
**Model**: {metadata['model_used']}  
**Genre**: {genre_line}  
**Writer level**: {sophistication}  
**Mode**: {mode_line}  
{"**Focus**: " + focus_line + "  " + chr(10) if focus_line else ""}**Dimensions analyzed**: {', '.join(metadata['dimensions_analyzed'])}  
**Total tokens**: {metadata['total_tokens']:,}

---

"""

        full_review = header + review_content
        save_review(full_review, output)

        # Success message
        click.echo(f"✅ Review complete!")
        click.echo(f"📁 Saved to: {output}")
        click.echo(f"📊 Actual tokens used: {metadata['total_tokens']:,}")
        click.echo(f"🏷️  Genre: {genre_line}")
        click.echo(f"🎯 Writer level: {sophistication}")
        click.echo(f"⚙️  Mode: {review_mode_used}")
        if is_mixed:
            click.echo(f"🔀 Mixed genre: {genre_used} + {secondary}")
        if dynamic_criteria:
            click.echo(f"🔬 Dynamic criteria: {', '.join(dynamic_criteria)}")

        # Show snippet of review
        click.echo("\n" + "=" * 60)
        click.echo("Preview of Top Priority Actions:")
        click.echo("=" * 60)
        lines = review_content.split('\n')
        in_priority_section = False
        priority_lines = []
        for line in lines:
            if 'Priority Actions' in line or 'Top 5' in line:
                in_priority_section = True
                continue
            if in_priority_section:
                if line.strip().startswith('##'):
                    break
                if line.strip():
                    priority_lines.append(line)

        for line in priority_lines[:5]:
            click.echo(line)
        click.echo("\n" + "=" * 60)
        click.echo(f"📄 See full review at: {output}")

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('essay_file', type=click.Path(exists=True))
@click.option('--dimensions', '-d', type=int, default=5,
              help='Number of dimensions to estimate (default: 5)')
@click.option('--genre', '-g',
              type=click.Choice(SUPPORTED_GENRES),
              default=None,
              help='Genre to estimate for (affects dimension count)')
def estimate(essay_file, dimensions, genre):
    """
    Estimate cost for reviewing an essay.

    Examples:
        python cli.py estimate my_essay.txt
        python cli.py estimate my_essay.txt --genre analytical
    """
    try:
        essay_text = read_essay(essay_file)
        word_count = len(essay_text.split())

        # If genre specified, use its dimension count
        if genre:
            num_dims = len(GENRE_CONFIGS[genre]["dimensions"])
        else:
            num_dims = dimensions

        api_key = get_api_key()
        reviewer = EssayReviewer(api_key=api_key)

        estimate_result = reviewer.estimate_cost(word_count, num_dims)

        click.echo(f"\n📊 Cost Estimate for: {Path(essay_file).name}")
        click.echo(f"{'=' * 50}")
        click.echo(f"Word count:           {word_count:,}")
        if genre:
            click.echo(f"Genre:                {genre}")
        click.echo(f"Review dimensions:    {num_dims}")
        click.echo(f"Estimated tokens:     ~{estimate_result['estimated_input_tokens'] + estimate_result['estimated_output_tokens']:,}")
        click.echo(f"  Input tokens:       ~{estimate_result['estimated_input_tokens']:,}")
        click.echo(f"  Output tokens:      ~{estimate_result['estimated_output_tokens']:,}")
        click.echo(f"\nEstimated cost:       £{estimate_result['cost_gbp']} (${estimate_result['cost_usd']})")
        click.echo(f"{'=' * 50}\n")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def setup():
    """
    Initial setup - create .env file for API key.
    """
    env_file = Path(__file__).parent / '.env'

    if env_file.exists():
        click.echo("⚠️  .env file already exists")
        if not click.confirm('Overwrite it?', default=False):
            return

    click.echo("\n🔑 Essay Reviewer Setup")
    click.echo("=" * 50)
    click.echo("\nYou need an Anthropic API key to use this tool.")
    click.echo("Get one at: https://console.anthropic.com/")
    click.echo()

    api_key = click.prompt("Enter your Anthropic API key", hide_input=True)

    with open(env_file, 'w') as f:
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")

    click.echo(f"\n✅ API key saved to {env_file}")
    click.echo("\n🚀 You're ready to go! Try:")
    click.echo("   python cli.py review your_essay.txt")


@cli.command()
def info():
    """
    Show information about supported genres and review dimensions.
    """
    click.echo("\n📋 Essay Reviewer v0.9.1 — Supported Genres & Dimensions")
    click.echo("=" * 60)
    click.echo("\n  Features: writer-level calibration, mixed genre handling, focus flag,")
    click.echo("            dynamic criteria generation, hybrid mode")

    for genre_key, config in GENRE_CONFIGS.items():
        click.echo(f"\n{'─' * 60}")
        click.echo(f"  {genre_key.upper()}")
        click.echo(f"  {config['description']}")
        click.echo(f"{'─' * 60}")

        dims, _, _ = load_genre_prompts(genre_key)
        for key, dim in dims.items():
            click.echo(f"\n  {dim['name']}  ({key})")
            click.echo(f"    Priority: {dim['priority']}")
            # Extract a brief description from the prompt
            prompt_text = dim['prompt']
            # Try to get the first substantive sentence after "Your focus:"
            if 'Your focus:' in prompt_text:
                focus = prompt_text.split('Your focus:')[1].strip()
                first_sentence = focus.split('.')[0].strip() + '.'
                if len(first_sentence) > 120:
                    first_sentence = first_sentence[:117] + '...'
                click.echo(f"    {first_sentence}")

    click.echo(f"\n{'=' * 60}")
    click.echo("\nUsage:")
    click.echo("  python cli.py review essay.txt                   # auto-detect genre")
    click.echo("  python cli.py review essay.txt --genre analytical # force genre")
    click.echo("  python cli.py review essay.txt --genre creative --focus \"imagery,ending\"")
    click.echo("  python cli.py review essay.txt --mode hybrid      # static + dynamic criteria")
    click.echo("  python cli.py review essay.txt --mode dynamic     # text-specific criteria only")
    click.echo("  python cli.py review essay.txt -d interpretive_depth -d framework_and_method")
    click.echo()


if __name__ == '__main__':
    cli()
