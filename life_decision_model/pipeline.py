"""
pipeline.py — run_model(): головна точка входу (розділ 5 / 17 документа).

Саме цю функцію імпортує сайт: `from scoring_model import run_model`.
Жодної Streamlit / анкети / LLM / PostgreSQL логіки тут немає (розділ 18
документа: межі відповідальності).
"""

from . import scoring


def run_model(user_profile: dict, scenarios: list) -> dict:
    """
    Приймає user_profile (dict, з user_profile.json) і scenarios
    (list[dict], з scenarios.json), повертає ranked_results (dict) у
    форматі розділу 15 документа: top_recommendation, ranked_scenarios,
    critical_areas, model_note.

    What-if (розділ 3.8 документа): окремої what-if-логіки не потрібно —
    сайт просто викликає run_model() ще раз зі зміненим user_profile:

        base_result = run_model(user_profile, scenarios)
        updated_result = run_model(modified_user_profile, scenarios)
    """
    return scoring.rank_scenarios(user_profile, scenarios)
