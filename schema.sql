-- Supabase / PostgreSQL schema for BalanceBrain MVP
-- Tables:
-- 1. user_profiles  — user profile JSON
-- 2. scenarios      — global and user-specific scenarios
-- 3. user_results   — saved deterministic model results

create table if not exists user_profiles (
    id bigint generated always as identity primary key,
    user_email text not null unique,
    data jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists scenarios (
    id bigint generated always as identity primary key,
    user_email text not null,
    title text not null,
    data jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists user_results (
    id bigint generated always as identity primary key,
    user_email text not null,
    profile_snapshot jsonb not null,
    scenarios_snapshot jsonb not null,
    model_result jsonb not null,
    created_at timestamptz not null default now()
);

-- Indexes for faster lookup by user_email

create index if not exists idx_user_profiles_user_email
on user_profiles(user_email);

create index if not exists idx_scenarios_user_email
on scenarios(user_email);

create index if not exists idx_user_results_user_email
on user_results(user_email);

create index if not exists idx_user_results_created_at
on user_results(created_at desc);

-- For hackathon MVP:
-- RLS is disabled so the app can read/write using anon public key.
-- Do not use this configuration for production without proper policies.

alter table user_profiles disable row level security;
alter table scenarios disable row level security;
alter table user_results disable row level security;