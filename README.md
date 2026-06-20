# \U0001F9ED AI Growth Advisor

Streamlit app: a **Gemini**-powered chat advisor + a deterministic decision
scoring engine, with the user's profile and scenario library stored in
**Supabase (Postgres)**.

## Quick start

### 1. Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create a Supabase project
1. Go to https://supabase.com \u2192 **New project** (remember the DB password).
2. Once the project is ready: **SQL Editor \u2192 New query** \u2192 paste the
   contents of [`schema.sql`](schema.sql) \u2192 **Run**. This creates the
   `user_profiles`, `scenarios`, and `user_results` tables, and **disables RLS**
   (Row-Level Security) so the `anon` key can write without auth.
3. **Project Settings \u2192 API**: copy the **Project URL** and the
   **anon public** key.

### 3. Gemini key
Get one at https://aistudio.google.com/apikey

### 4. Secrets
Copy `.env.example` to `.env` and fill in your values (no quotes, no spaces):
```
GEMINI_API_KEY=AIza...        # Gemini keys always start with "AIza"
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=...
```
> On Streamlit Community Cloud, add the same keys under
> **Settings \u2192 Secrets** instead of `.env` \u2014 the code reads both
> sources automatically.

### 5. Load the scenario library
The decision simulation needs scenarios in the full scoring-model format.
Load the built-in library once:
```bash
python seed_scenarios.py
```
This is safe to re-run any time \u2014 it upserts by scenario name.

### 6. Run
```bash
streamlit run app.py
```

## How to use it
1. In the sidebar, enter your **email** (used as your user id).
2. **Profile** tab \u2014 fill in the questionnaire (balance wheel, focus area,
   resources, working style) \u2192 **Save profile**.
3. **Chat** tab \u2014 click **Run decision simulation** to rank the shared
   scenarios against your profile, or just chat with the Gemini-powered
   advisor, which sees your profile and notes.

## Chat behavior
The chat replies **briefly and clearly** (2\u20134 sentences / up to 4 bullet
points), stays on the topic of personal development, and declines unrelated
requests. Configuration lives in `llm.py`:
- `MODEL` \u2014 the model (`gemini-2.5-flash`, can use `gemini-2.5-pro`);
- `SYSTEM_BASE` \u2014 tone/format instructions;
- `temperature`, `max_output_tokens`, `thinking_config` \u2014 inside `chat()`.
- `thinking_budget=0` disables model "thinking" \u2014 without this, short
  replies get truncated because thinking eats into `max_output_tokens`.

## Troubleshooting
- **`API key not valid`** \u2014 the Gemini key is wrong. It must start with
  `AIza` (get one at https://aistudio.google.com/apikey).
- **`row violates row-level security policy`** \u2014 RLS wasn't disabled. Run
  in the Supabase SQL Editor:
  ```sql
  alter table user_profiles disable row level security;
  alter table scenarios disable row level security;
  alter table user_results disable row level security;
  ```
- **`Name or service not known` / `ConnectError`** \u2014 `SUPABASE_URL` is
  wrong, has a placeholder value, or has stray quotes/whitespace. Re-copy it
  from Supabase \u2192 Project Settings \u2192 API.
- **No scenarios found for the simulation** \u2014 run `python seed_scenarios.py`
  to load the scenario library into Supabase.
- **Empty / truncated chat replies** \u2014 make sure `chat()` includes
  `thinking_config=types.ThinkingConfig(thinking_budget=0)`.

## Structure
| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI (questionnaire + chat) |
| `llm.py` | Gemini wrapper (system prompt + context) |
| `db.py` | Supabase: save/load profile, scenarios, results |
| `models.py` | `UserProfile`, `Scenario` data classes |
| `config.py` | Reads secrets (st.secrets / .env) |
| `decision_engine.py` | Runs the scoring model + LLM explanation |
| `seed_scenarios.py` | Loads the shared scenario library into Supabase |
| `life_decision_model/` | Deterministic scoring engine (Goal Fit, Balance Score, Feasibility, Readiness, Action Style Fit, Reversibility, Risk Penalty) |
| `schema.sql` | Supabase tables + RLS disabled |

## What's next (out of current scope)
Comparing scenarios side by side, semantic search over the scenario
library, letting users add their own scoring-ready scenarios from the UI.
