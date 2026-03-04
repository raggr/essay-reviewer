"""
storage.py — Supabase persistence for essay reviews.

Stores essays and reviews only when the user has explicitly opted in.
Requires two environment variables:
    SUPABASE_URL   — e.g. https://xxxx.supabase.co
    SUPABASE_KEY   — service role key (anon key also works for insert-only)

If either variable is missing, storage silently does nothing so the app
remains fully functional without a database configured.

Supabase table schema (run once in the Supabase SQL editor):

    create table public.reviews (
        id            uuid primary key default gen_random_uuid(),
        created_at    timestamptz not null default now(),
        word_count    integer,
        genre         text,
        register      text,
        writer_level  text,
        review_mode   text,
        model         text,
        total_tokens  integer,
        dynamic_criteria text[],
        essay_text    text,
        review_text   text
    );

    -- Row-level security: service role key bypasses RLS.
    -- If using anon key, also run:
    -- alter table public.reviews enable row level security;
    -- create policy "insert only" on public.reviews for insert with check (true);
"""

import os

_client = None
_ready = False


def _get_client():
    global _client, _ready
    if _ready:
        return _client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url or not key:
        print("[storage] SUPABASE_URL or SUPABASE_KEY not set — storage disabled.")
        _ready = True
        _client = None
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        print(f"[storage] Supabase connected: {url}")
    except Exception as e:
        print(f"[storage] Failed to connect to Supabase: {e}")
        _client = None

    _ready = True
    return _client


def save_review(essay_text: str, result: dict) -> bool:
    """
    Persist an essay + review to Supabase.
    Called only when the user has opted in.
    Returns True on success, False on failure (non-fatal).
    """
    client = _get_client()
    if client is None:
        return False

    meta = result.get("metadata", {})
    genre_meta = meta.get("genre_metadata", {})

    row = {
        "word_count":       meta.get("word_count"),
        "genre":            meta.get("genre"),
        "register":         genre_meta.get("register"),
        "writer_level":     meta.get("writer_level"),
        "review_mode":      meta.get("review_mode"),
        "model":            meta.get("model"),
        "total_tokens":     meta.get("total_tokens"),
        "dynamic_criteria": meta.get("dynamic_criteria"),  # list or None
        "essay_text":       essay_text,
        "review_text":      result.get("report", ""),
    }

    try:
        client.table("reviews").insert(row).execute()
        print(f"[storage] Saved review ({row['word_count']} words, {row['genre']})")
        return True
    except Exception as e:
        print(f"[storage] Insert failed: {e}")
        return False
