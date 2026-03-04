"""
Prompt modules for essay review.

Backward-compatible re-exports so existing code that does
  from prompts import MASTER_SYSTEM_PROMPT
continues to work.
"""
from .shared import MASTER_SYSTEM_PROMPT, FALSE_FLAG_FILTER_PROMPT
from .argumentative import DIMENSION_PROMPTS, SYNTHESIS_PROMPT, INLINE_COMMENT_PROMPT
