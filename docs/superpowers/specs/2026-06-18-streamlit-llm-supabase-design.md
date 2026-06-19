# Streamlit + Gemini + Supabase — Design

**Date:** 2026-06-18
**Status:** Approved

## Goal
Connect an LLM chat (Gemini) to a Streamlit app, backed by a Supabase/Postgres
database that stores scenarios and saves user profiles. Scope: plumbing +
profile questionnaire (анкета). No scoring formulas, no vector search yet.

## Stack
- Streamlit (UI)
- Google Gemini via `google-genai` SDK
- Supabase (Postgres) via `supabase-py`

## Structure
```
app.py        # Streamlit: tabs — Профіль (form) + Чат
llm.py        # Gemini wrapper (system prompt + profile/scenario context)
db.py         # Supabase client: save/load profile, list/save scenarios
models.py     # UserProfile, Scenario dataclasses
schema.sql    # Supabase tables
requirements.txt
.env.example  # GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

## Data (2 tables, JSONB payloads)
- `user_profiles`: id, user_email, data (jsonb: balance wheel, focus, factors), created_at
- `scenarios`: id, user_email, title, data (jsonb: goal_tags, requirements, style, risk), created_at

User identity = email (no auth yet).

## Flow
1. **Профіль tab** — questionnaire form → save to `user_profiles`.
2. **Чат tab** — `st.chat_input` + history in session_state. Before each reply,
   load saved profile + scenarios and inject into the Gemini system prompt.
   Gemini answers as a consultant aware of the user's profile.

## Secrets
Read via `st.secrets` with fallback to `os.environ` (.env loaded by dotenv).
No keys in git.

## Out of scope (next step)
Scoring formulas, scenario comparison, vector/semantic search.
