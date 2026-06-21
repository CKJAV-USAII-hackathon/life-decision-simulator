from __future__ import annotations

import json
from typing import Any

import db
import llm
from life_decision_model import run_model


def _json_safe(obj: Any) -> Any:
    """
    Makes an object safe to store in JSONB.
    """
    return json.loads(json.dumps(obj, ensure_ascii=False))


def run_user_simulation_with_explanation(user_email: str) -> dict[str, Any]:
    """
    1. Loads profile and scenarios from Supabase.
    2. Runs the scoring model.
    3. Saves the raw model result to user_results.
    4. Passes the model result to the LLM.
    5. Returns the LLM explanation for the chat, but doesn't save it to the DB.
    """
    user_profile = db.load_model_profile_data(user_email)
    if not user_profile:
        raise ValueError(
            f"No profile found for user_email='{user_email}'. "
            "Save a profile on the Profile tab first."
        )

    scenarios = db.list_model_scenarios_data(user_email)
    if not scenarios:
        raise ValueError(
            "No scenarios found in the scoring model format. "
            "Run `python seed_scenarios.py` to load the shared scenario library."
        )

    model_result = run_model(user_profile, scenarios)

    user_profile_safe = _json_safe(user_profile)
    scenarios_safe = _json_safe(scenarios)
    model_result_safe = _json_safe(model_result)

    saved_row = db.save_user_result(
        user_email=user_email,
        profile_snapshot=user_profile_safe,
        scenarios_snapshot=scenarios_safe,
        model_result=model_result_safe,
    )

    explanation = llm.explain_model_result(
        model_result=model_result_safe,
        profile_data=user_profile_safe,
    )

    return {
        "result_id": saved_row.get("id"),
        "model_result": model_result_safe,
        "explanation": explanation,
    }
