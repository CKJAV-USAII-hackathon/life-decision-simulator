"""Database layer \u2014 Supabase (Postgres).

Saves/loads profiles and scenarios. All payloads live in the JSONB column
`data`; conversion happens in models.py.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from config import get_secret
from models import Scenario, UserProfile

GLOBAL_USER_EMAIL = "__global__"


@lru_cache(maxsize=1)
def get_client() -> Client:
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_KEY are not set. Add them to .env or st.secrets."
        )
    return create_client(url, key)


# ---------- Profiles ----------

def save_profile(profile: UserProfile) -> None:
    """Upsert the profile by user_email."""
    client = get_client()
    payload = {
        "user_email": profile.user_email,
        "data": profile.to_data(),
    }
    client.table("user_profiles").upsert(
        payload, on_conflict="user_email").execute()


def load_profile(user_email: str) -> UserProfile | None:
    client = get_client()
    res = (
        client.table("user_profiles")
        .select("*")
        .eq("user_email", user_email)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    return UserProfile.from_row(rows[0]) if rows else None


# ---------- Scenarios ----------

def save_scenario(scenario: Scenario) -> None:
    client = get_client()
    payload = {
        "user_email": scenario.user_email,
        "title": scenario.title,
        "data": scenario.to_data(),
    }
    client.table("scenarios").insert(payload).execute()


def list_scenarios(user_email: str) -> list[Scenario]:
    """Loads global scenarios + scenarios for this specific user."""
    client = get_client()
    res = (
        client.table("scenarios")
        .select("*")
        .in_("user_email", [GLOBAL_USER_EMAIL, user_email])
        .order("created_at", desc=True)
        .execute()
    )
    return [Scenario.from_row(r) for r in (res.data or [])]

# ---------- Data for the scoring model ----------


def load_model_profile_data(user_email: str) -> dict | None:
    """
    Loads the raw JSONB profile in the exact shape the scoring model
    expects (this is the same shape produced by UserProfile.to_data()).
    """
    client = get_client()
    res = (
        client.table("user_profiles")
        .select("*")
        .eq("user_email", user_email)
        .limit(1)
        .execute()
    )

    rows = res.data or []
    if not rows:
        return None

    data = rows[0].get("data", {}) or {}

    # Fallback in case user_id wasn't set inside the JSON.
    data.setdefault("user_id", user_email)

    return data


def list_model_scenarios_data(user_email: str) -> list[dict]:
    """
    Loads raw JSONB scenarios in the format the scoring model expects.
    Takes global scenarios + scenarios for this specific user.

    Skips short legacy-format scenarios that don't have the required fields.
    """
    client = get_client()
    res = (
        client.table("scenarios")
        .select("*")
        .in_("user_email", [GLOBAL_USER_EMAIL, user_email])
        .order("created_at", desc=True)
        .execute()
    )

    scenarios: list[dict] = []

    for row in (res.data or []):
        data = row.get("data", {}) or {}

        required_fields = [
            "scenario_id",
            "goal_tags",
            "time_required_per_week",
            "budget_required",
            "skill_required",
            "intensity",
            "impact",
            "reversibility",
            "uncertainty_level",
        ]

        # Skip legacy short-format scenarios:
        # goal_tags / requirements / style / risk
        if not all(field in data for field in required_fields):
            continue

        # Safe defaults for optional fields.
        data.setdefault("name", row.get(
            "title", data.get("scenario_id", "Unnamed scenario")))
        data.setdefault("category", "")
        data.setdefault("best_for_requests", [])
        data.setdefault("preferred_formats", [])
        data.setdefault("structure_level", 3)
        data.setdefault("social_intensity", 3)
        data.setdefault("feedback_level", 3)
        data.setdefault("risk_tags", [])
        data.setdefault("not_recommended_if", [])
        data.setdefault("main_benefit", "")
        data.setdefault("main_cost", "")
        data.setdefault("tradeoffs", [])
        data.setdefault("first_step", "")

        scenarios.append(data)

    return scenarios

# ---------- Scoring model results ----------


def save_user_result(
    user_email: str,
    profile_snapshot: dict,
    scenarios_snapshot: list[dict],
    model_result: dict,
) -> dict:
    """
    Saves the result of a scoring model run to Supabase.
    Stores only the structured model output, without the LLM explanation.
    """
    client = get_client()

    payload = {
        "user_email": user_email,
        "profile_snapshot": profile_snapshot,
        "scenarios_snapshot": scenarios_snapshot,
        "model_result": model_result,
    }

    res = client.table("user_results").insert(payload).execute()
    rows = res.data or []
    return rows[0] if rows else {}
