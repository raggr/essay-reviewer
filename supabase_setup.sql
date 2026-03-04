-- Run this once in the Supabase SQL Editor (supabase.com → your project → SQL Editor)

create table public.reviews (
    id               uuid primary key default gen_random_uuid(),
    created_at       timestamptz not null default now(),
    word_count       integer,
    genre            text,
    register         text,
    writer_level     text,
    review_mode      text,
    model            text,
    total_tokens     integer,
    dynamic_criteria text[],
    essay_text       text,
    review_text      text
);

-- Optional: enable row-level security if using the anon key instead of service role key
-- alter table public.reviews enable row level security;
-- create policy "insert only" on public.reviews for insert with check (true);
