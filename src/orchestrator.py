"""
Core orchestrator for essay reviews — genre-aware pipeline.

v0.9.0: Dynamic criteria generation + hybrid mode.
v0.8.3: 6-genre support (creative, reflective added). Focus flag.
v0.8.2: Writer-level calibration + mixed genre handling.

Phase 0: Genre detection  (1 API call — returns genre, secondary genre, writer level)
Phase 0.5 (conditional): Dynamic criteria generation (1 API call — when genre is mixed/low-confidence or hybrid mode)
Phase 1: Parallel dimension reviews (5-10+ concurrent API calls, genre-specific, dynamic, or both)
Phase 2: Calibrated synthesis  (1 API call, writer-level adjusted)
Phase 3: False-flag filter (1 API call, genre-agnostic)

Import compatibility: works both as `src.orchestrator` (relative imports)
and as `orchestrator` (when src/ is on sys.path via absolute imports).
"""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import anthropic

try:
    from .prompts.shared import FALSE_FLAG_FILTER_PROMPT
    from .pipeline import (
        load_genre_prompts,
        load_synthesis_system_message,
        build_dimension_system_prompt,
        load_mixed_genre_prompts,
        build_calibrated_synthesis_prompt,
        should_run_mixed_genre,
        should_use_dynamic_criteria,
        should_use_static_genre,
        get_static_genre_for_hybrid,
        build_hybrid_synthesis_prompt,
        build_dynamic_synthesis_with_calibration,
    )
    from .genre_detection import (
        GENRE_DETECTION_SYSTEM,
        GENRE_DETECTION_USER,
        DEFAULT_GENRE_METADATA,
        parse_genre_response,
    )
    from .dynamic_criteria import (
        CRITERIA_GENERATION_SYSTEM,
        CRITERIA_GENERATION_USER,
        DYNAMIC_SYNTHESIS_PROMPT,
        DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE,
        parse_criteria_response,
        criteria_to_dimension_prompts,
    )
    from .config import (
        DEFAULT_GENRE, SUPPORTED_GENRES, DEFAULT_WRITER_LEVEL,
        REVIEW_MODE_STANDARD, REVIEW_MODE_DYNAMIC, REVIEW_MODE_HYBRID,
    )
except ImportError:
    from prompts.shared import FALSE_FLAG_FILTER_PROMPT
    from pipeline import (
        load_genre_prompts,
        load_synthesis_system_message,
        build_dimension_system_prompt,
        load_mixed_genre_prompts,
        build_calibrated_synthesis_prompt,
        should_run_mixed_genre,
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


@dataclass
class ReviewResult:
    """Result from a single review dimension"""
    dimension: str
    feedback: str
    tokens_used: int
    success: bool
    genre_source: str = ""
    error: Optional[str] = None


class EssayReviewer:
    """Orchestrates parallel essay reviews across multiple dimensions"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        genre_override: Optional[str] = None,
        review_mode: str = REVIEW_MODE_STANDARD,
    ):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.genre_override = genre_override
        self.review_mode = review_mode

    async def review_essay(
        self,
        essay_text: str,
        dimensions: Optional[List[str]] = None,
        max_tokens_per_review: int = 6000,
        max_tokens_synthesis: int = 16000,
        focus: Optional[str] = None,
    ) -> Dict:
        """Main entry point for essay review."""

        # ── Phase 0: Genre detection ──────────────────────────────
        if self.genre_override and self.genre_override in SUPPORTED_GENRES:
            genre = self.genre_override
            genre_metadata = dict(DEFAULT_GENRE_METADATA)
            genre_metadata["genre"] = genre
            genre_metadata["confidence"] = 1.0
            detect_tokens = 0
            print(f"Genre override: {genre}")
        else:
            print("Detecting genre...")
            genre_metadata, detect_tokens = await self._detect_genre(essay_text)
            genre = genre_metadata.get("genre", DEFAULT_GENRE)
            if genre not in SUPPORTED_GENRES and genre != "mixed":
                print(f"Detected genre '{genre}' not yet supported — falling back to {DEFAULT_GENRE}")
                genre = DEFAULT_GENRE
            else:
                register = genre_metadata.get("register", "unknown")
                confidence = genre_metadata.get("confidence", 0)
                writer_level = genre_metadata.get("writer_level", DEFAULT_WRITER_LEVEL)
                secondary = genre_metadata.get("secondary_genre")
                sec_conf = genre_metadata.get("secondary_genre_confidence", 0)
                print(f"Detected genre: {genre} (register: {register}, confidence: {confidence:.0%})")
                print(f"Writer level: {writer_level}")
                if secondary:
                    print(f"Secondary genre: {secondary} (confidence: {sec_conf:.0%})")

        # ── Determine review path ─────────────────────────────────
        writer_level = genre_metadata.get("writer_level", DEFAULT_WRITER_LEVEL)
        use_dynamic = should_use_dynamic_criteria(genre_metadata, self.review_mode)
        use_static = should_use_static_genre(genre_metadata, self.review_mode)
        is_hybrid = use_dynamic and use_static

        # Determine mixed-genre routing for static path
        is_mixed_genre = (
            use_static
            and not self.genre_override
            and not is_hybrid  # hybrid replaces mixed-genre routing
            and should_run_mixed_genre(genre_metadata)
        )
        secondary_genre = genre_metadata.get("secondary_genre") if is_mixed_genre else None

        if is_hybrid:
            print(f"Hybrid mode: running static ({genre}) + dynamic criteria")
        elif use_dynamic and not use_static:
            print("Dynamic criteria mode: generating text-specific evaluation criteria")
        elif is_mixed_genre:
            print(f"Mixed genre detected — running {genre} + {secondary_genre} dimensions")

        # ── Phase 0.5 (conditional): Generate dynamic criteria ────
        dynamic_dim_prompts = {}
        criteria_tokens = 0
        generated_criteria = None

        if use_dynamic:
            print("Generating dynamic evaluation criteria...")
            generated_criteria, criteria_tokens = await self._generate_criteria(essay_text)
            if generated_criteria:
                dynamic_dim_prompts = criteria_to_dimension_prompts(generated_criteria)
                criteria_names = [c["name"] for c in generated_criteria]
                print(f"Generated {len(generated_criteria)} criteria: {', '.join(criteria_names)}")
            else:
                print("Dynamic criteria generation failed — falling back to static genre path")
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

            if is_mixed_genre:
                mixed = load_mixed_genre_prompts(genre, secondary_genre)
                primary_dim_prompts = mixed["primary_prompts"]
                secondary_dim_prompts = mixed["secondary_prompts"]
                synthesis_prompt = mixed["primary_synthesis"]
                synthesis_system_message = mixed["primary_system_message"]
                genre_used = mixed["primary_genre"]
            else:
                primary_dim_prompts, synthesis_prompt, genre_used = load_genre_prompts(static_genre)
                synthesis_system_message = load_synthesis_system_message(genre_used)

        # ── Build synthesis prompt ────────────────────────────────
        word_count = len(essay_text.split())

        if is_hybrid:
            # Hybrid: use dynamic synthesis prompt base + hybrid context
            calibrated_synthesis = build_hybrid_synthesis_prompt(
                DYNAMIC_SYNTHESIS_PROMPT,
                writer_level,
                static_genre=genre_used,
                focus=focus,
                word_count=word_count,
            )
            synthesis_system_message = DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE
        elif use_dynamic and not use_static:
            # Dynamic only: use dynamic synthesis with calibration
            calibrated_synthesis = build_dynamic_synthesis_with_calibration(
                writer_level,
                focus=focus,
                word_count=word_count,
            )
            synthesis_system_message = DYNAMIC_SYNTHESIS_SYSTEM_MESSAGE
        else:
            # Static path (standard or mixed-genre)
            calibrated_synthesis = build_calibrated_synthesis_prompt(
                synthesis_prompt,
                writer_level,
                is_mixed_genre=is_mixed_genre,
                primary_genre=genre_used,
                secondary_genre=secondary_genre,
                focus=focus,
                word_count=word_count,
            )

        if focus:
            print(f"Focus areas: {focus}")

        # ── Phase 1: Parallel dimension reviews ───────────────────
        review_tasks = []

        # Static genre dimensions
        if use_static and primary_dim_prompts:
            if dimensions is not None:
                primary_dims = [d for d in dimensions if d in primary_dim_prompts]
                if not primary_dims:
                    primary_dims = list(primary_dim_prompts.keys())
            else:
                primary_dims = list(primary_dim_prompts.keys())

            review_tasks.extend([
                self._run_dimension_review(
                    dim, primary_dim_prompts, essay_text, max_tokens_per_review,
                    genre_source=genre_used,
                )
                for dim in primary_dims
            ])

            # Secondary genre dimensions (mixed-genre only)
            if is_mixed_genre and secondary_dim_prompts:
                secondary_dims = list(secondary_dim_prompts.keys())
                review_tasks.extend([
                    self._run_dimension_review(
                        dim, secondary_dim_prompts, essay_text, max_tokens_per_review,
                        genre_source=secondary_genre,
                    )
                    for dim in secondary_dims
                ])

        # Dynamic criteria dimensions
        if use_dynamic and dynamic_dim_prompts:
            dynamic_dims = list(dynamic_dim_prompts.keys())
            review_tasks.extend([
                self._run_dimension_review(
                    dim, dynamic_dim_prompts, essay_text, max_tokens_per_review,
                    genre_source="dynamic",
                )
                for dim in dynamic_dims
            ])

        total_dims = len(review_tasks)
        print(f"Running {total_dims} review dimensions...")

        dimension_results = await asyncio.gather(*review_tasks, return_exceptions=True)

        successful_results = []
        for result in dimension_results:
            if isinstance(result, Exception):
                print(f"Warning: dimension review failed: {str(result)}")
            else:
                successful_results.append(result)

        if not successful_results:
            raise Exception("All review dimensions failed")

        print(f"Completed {len(successful_results)}/{total_dims} reviews successfully")

        # ── Phase 2: Calibrated synthesis ─────────────────────────
        print(f"Synthesizing results (writer level: {writer_level})...")
        synthesis = await self._synthesize_reviews(
            essay_text,
            successful_results,
            calibrated_synthesis,
            synthesis_system_message,
            max_tokens_synthesis,
        )

        # ── Phase 3: False-flag filter ────────────────────────────
        print("Filtering false flags...")
        filtered_synthesis, filter_tokens = await self._filter_false_flags(synthesis)

        # ── Build result ──────────────────────────────────────────
        total_tokens = (
            detect_tokens
            + criteria_tokens
            + sum(r.tokens_used for r in successful_results)
            + filter_tokens
        )

        # Determine the review mode actually used
        if is_hybrid:
            mode_used = REVIEW_MODE_HYBRID
        elif use_dynamic and not use_static:
            mode_used = REVIEW_MODE_DYNAMIC
        else:
            mode_used = REVIEW_MODE_STANDARD

        return {
            "summary_and_inline": filtered_synthesis,
            "individual_reviews": [
                {
                    "dimension": r.dimension,
                    "feedback": r.feedback,
                    "tokens": r.tokens_used,
                    "genre_source": r.genre_source,
                }
                for r in successful_results
            ],
            "metadata": {
                "word_count": len(essay_text.split()),
                "dimensions_analyzed": [r.dimension for r in successful_results],
                "total_tokens": total_tokens,
                "model_used": self.model,
                "genre": genre_used,
                "genre_metadata": genre_metadata,
                "is_mixed_genre": is_mixed_genre,
                "secondary_genre": secondary_genre,
                "writer_level": writer_level,
                "focus": focus,
                "review_mode": mode_used,
                "dynamic_criteria": [c["name"] for c in generated_criteria] if generated_criteria else None,
            },
        }

    # ── Phase 0 helper ────────────────────────────────────────────

    async def _detect_genre(self, essay_text: str) -> tuple:
        """Classify genre, secondary genre, and writer level via a single API call."""
        try:
            user_prompt = GENRE_DETECTION_USER.format(essay_text=essay_text)

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=800,
                temperature=0.1,
                system=GENRE_DETECTION_SYSTEM,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                response = await stream.get_final_message()

            raw_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            metadata = parse_genre_response(raw_text)
            return metadata, tokens_used

        except Exception as e:
            print(f"Genre detection failed ({e}), falling back to {DEFAULT_GENRE}")
            return dict(DEFAULT_GENRE_METADATA), 0

    # ── Phase 0.5 helper: Dynamic criteria generation ─────────────

    async def _generate_criteria(self, essay_text: str) -> tuple:
        """
        Generate text-specific evaluation criteria via API call.

        Returns:
            Tuple of (criteria list or None, tokens_used int)
        """
        try:
            user_prompt = CRITERIA_GENERATION_USER.format(essay_text=essay_text)

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=CRITERIA_GENERATION_SYSTEM,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                response = await stream.get_final_message()

            raw_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            criteria = parse_criteria_response(raw_text)
            return criteria, tokens_used

        except Exception as e:
            print(f"Criteria generation failed: {e}")
            return None, 0

    # ── Phase 1 helper ────────────────────────────────────────────

    async def _run_dimension_review(
        self,
        dimension_key: str,
        dimension_prompts: Dict,
        essay_text: str,
        max_tokens: int,
        genre_source: str = "",
    ) -> ReviewResult:
        """Execute a single review dimension."""
        dimension = dimension_prompts[dimension_key]

        try:
            system_prompt = build_dimension_system_prompt(dimension["prompt"])
            user_message = f"Essay to review:\n\n{essay_text}"

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = await stream.get_final_message()

            feedback = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return ReviewResult(
                dimension=dimension["name"],
                feedback=feedback,
                tokens_used=tokens_used,
                success=True,
                genre_source=genre_source,
            )

        except Exception as e:
            return ReviewResult(
                dimension=dimension["name"],
                feedback="",
                tokens_used=0,
                success=False,
                genre_source=genre_source,
                error=str(e),
            )

    # ── Phase 2 helper ────────────────────────────────────────────

    async def _synthesize_reviews(
        self,
        essay_text: str,
        reviews: List[ReviewResult],
        synthesis_prompt_template: str,
        synthesis_system_message: str,
        max_tokens: int,
    ) -> str:
        """Combine all dimension reviews into final report."""
        has_mixed = any(r.genre_source for r in reviews)
        if has_mixed:
            reviews_text = "\n\n".join(
                [f"### {r.dimension} [{r.genre_source}]\n{r.feedback}"
                 for r in reviews if r.success]
            )
        else:
            reviews_text = "\n\n".join(
                [f"### {r.dimension}\n{r.feedback}" for r in reviews if r.success]
            )

        synthesis_prompt = synthesis_prompt_template.format(
            num_reviews=len(reviews),
            essay_text=essay_text,
            reviews=reviews_text,
        )

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.3,
            system=synthesis_system_message,
            messages=[{"role": "user", "content": synthesis_prompt}],
        ) as stream:
            response = await stream.get_final_message()

        return response.content[0].text

    # ── Phase 3 helper ────────────────────────────────────────────

    async def _filter_false_flags(
        self, report_text: str, max_tokens: int = 16000
    ) -> tuple:
        """Post-synthesis pass: remove observations based on outdated training knowledge."""
        prompt = FALSE_FLAG_FILTER_PROMPT.format(report=report_text)

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.1,
            system=(
                "You are a quality-control editor. Your only job is to identify and "
                "remove false flags from a draft review — observations where the reviewer "
                "flagged something as an error because of outdated training data rather "
                "than a genuine problem with the essay. Remove false flags. Keep everything "
                "else exactly as-is."
            ),
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = await stream.get_final_message()

        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        return response.content[0].text, tokens_used

    # ── Cost estimation ───────────────────────────────────────────

    def estimate_cost(
        self, word_count: int, num_dimensions: int = 5, is_mixed: bool = False,
        review_mode: str = REVIEW_MODE_STANDARD,
    ) -> Dict[str, float]:
        """Estimate cost for reviewing an essay."""
        if is_mixed:
            num_dimensions = num_dimensions * 2
        if review_mode == REVIEW_MODE_HYBRID:
            # Static dims + dynamic dims + criteria generation call
            num_dimensions = num_dimensions + 5
        elif review_mode == REVIEW_MODE_DYNAMIC:
            num_dimensions = 5  # dynamic always generates 5

        essay_tokens = int(word_count * 1.3)
        input_tokens = (essay_tokens * (num_dimensions + 1)) + (4000 * num_dimensions)
        output_tokens = (3000 * num_dimensions) + 6000 + 500

        # Add criteria generation cost for dynamic/hybrid
        if review_mode in (REVIEW_MODE_DYNAMIC, REVIEW_MODE_HYBRID):
            input_tokens += essay_tokens + 2000  # criteria generation input
            output_tokens += 1500  # criteria generation output

        input_cost_usd = (input_tokens / 1_000_000) * 3
        output_cost_usd = (output_tokens / 1_000_000) * 15
        total_cost_usd = input_cost_usd + output_cost_usd
        total_cost_gbp = total_cost_usd * 0.79

        return {
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "cost_usd": round(total_cost_usd, 2),
            "cost_gbp": round(total_cost_gbp, 2),
            "is_mixed_genre": is_mixed,
            "review_mode": review_mode,
        }
