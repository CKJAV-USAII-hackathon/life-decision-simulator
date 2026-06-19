from __future__ import annotations

import json
from typing import Any

import db
import llm
from life_decision_model import run_model


def _json_safe(obj: Any) -> Any:
    """
    Робить об'єкт безпечним для збереження в JSONB.
    """
    return json.loads(json.dumps(obj, ensure_ascii=False))


def run_user_simulation_with_explanation(user_email: str) -> dict[str, Any]:
    """
    1. Бере profile і scenarios з Supabase.
    2. Запускає scoring model.
    3. Зберігає raw model result у user_results.
    4. Передає model result в LLM.
    5. Повертає LLM explanation у чат, але не зберігає її в БД.
    """
    user_profile = db.load_model_profile_data(user_email)
    if not user_profile:
        raise ValueError(
            f"Не знайдено профіль для user_email='{user_email}'. "
            "Створи запис у таблиці user_profiles."
        )

    scenarios = db.list_model_scenarios_data(user_email)
    if not scenarios:
        raise ValueError(
            "Не знайдено сценаріїв у форматі scoring model. "
            "Додай сценарії в таблицю scenarios з user_email='__global__' "
            "або з поточним email."
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
