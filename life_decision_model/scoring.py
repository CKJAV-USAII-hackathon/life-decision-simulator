"""
scoring.py — фінальна scoring formula (розділ 13 / 21.6) і ранжування
сценаріїв (розділ 15: top_recommendation / ranked_scenarios / critical_areas
/ model_note).

Імпортує gaps.py + metrics.py (розділ 4 архітектури).
"""

from . import config
from . import gaps as gaps_module
from . import metrics


def _risk_level(risk_penalty: float) -> str:
    """
    Переводить risk_penalty у risk_level для product-шару (UI/warnings).

    Пороги — робоча домовленість для MVP (config.RISK_LEVEL_*), документ
    точних меж не фіксує; легко змінити окремо від формули Risk Penalty.
    """
    if risk_penalty < config.RISK_LEVEL_LOW_MAX:
        return "low"
    if risk_penalty < config.RISK_LEVEL_MEDIUM_MAX:
        return "medium"
    return "high"


def _build_warnings(user_profile: dict, scenario: dict, critical_areas: list) -> list:
    """
    Формує текстові warnings на основі тих самих сигналів, що і Risk
    Penalty (critical area harm / overload / uncertainty), плюс risk_tags
    і not_recommended_if зі scenario.

    Для MVP це лише попередження, не штраф у самій формулі — питання, чи
    risk_tags/hidden_concerns/not_recommended_if додавати в математику
    Risk Penalty, ще не вирішено (розділ 6 архітектурного документа).
    """
    warnings = []
    impact = scenario.get("impact", {})

    harmed_critical_areas = [a for a in critical_areas if impact.get(a, 0) < 0]
    if harmed_critical_areas:
        warnings.append(
            "Сценарій погіршує critical area(s): "
            + ", ".join(harmed_critical_areas)
        )

    if metrics.overload_risk(user_profile, scenario) >= 0.5:
        warnings.append("Високий ризик перевантаження (energy / time / intensity).")

    if metrics.uncertainty_risk(scenario) >= 0.5:
        warnings.append("Висока невизначеність і низька reversibility сценарію.")

    for tag in scenario.get("risk_tags", []):
        warnings.append(f"risk_tag: {tag}")

    hidden_concerns = set(user_profile.get("hidden_concerns", []))
    overlapping_not_recommended = [
        c for c in scenario.get("not_recommended_if", []) if c in hidden_concerns
    ]
    if overlapping_not_recommended:
        warnings.append(
            "Сценарій позначений not_recommended_if для: "
            + ", ".join(overlapping_not_recommended)
            + " — це збігається з hidden_concerns користувача."
        )

    return warnings


def score_scenario(
    user_profile: dict,
    scenario: dict,
    gaps: dict,
    critical_areas: list,
) -> dict:
    """
    Рахує всі сім метрик для одного сценарію (gaps/critical_areas рахуються
    зовні один раз і передаються сюди), фінальний score за формулою
    розділу 13/21.6, переводить у 0..100, формує structured result для
    цього сценарію (score_breakdown, warnings, risk_level — розділ 15).
    """
    goal_fit = metrics.compute_goal_fit(user_profile, scenario)
    balance_score = metrics.compute_balance_score(user_profile, scenario, gaps, critical_areas)
    feasibility = metrics.compute_feasibility(user_profile, scenario)
    readiness = metrics.compute_readiness(user_profile, scenario)
    action_style_fit = metrics.compute_action_style_fit(user_profile, scenario)
    reversibility = metrics.compute_reversibility_score(scenario)
    risk_penalty = metrics.compute_risk_penalty(user_profile, scenario, critical_areas)

    w = config.FINAL_SCORE_WEIGHTS
    final_score = (
        w["goal_fit"] * goal_fit
        + w["balance_score"] * balance_score
        + w["feasibility"] * feasibility
        + w["action_style_fit"] * action_style_fit
        + w["readiness"] * readiness
        + w["reversibility"] * reversibility
        - risk_penalty
    )
    final_score = metrics.clamp(final_score)
    final_score_100 = round(final_score * 100)

    return {
        "scenario_id": scenario.get("scenario_id"),
        "name": scenario.get("name"),
        "final_score": final_score_100,
        "score_breakdown": {
            "goal_fit": goal_fit,
            "balance_score": balance_score,
            "feasibility": feasibility,
            "readiness": readiness,
            "action_style_fit": action_style_fit,
            "reversibility": reversibility,
            "risk_penalty": risk_penalty,
        },
        "risk_level": _risk_level(risk_penalty),
        "warnings": _build_warnings(user_profile, scenario, critical_areas),
        "main_benefit": scenario.get("main_benefit"),
        "main_cost": scenario.get("main_cost"),
        "tradeoffs": scenario.get("tradeoffs", []),
        "first_step": scenario.get("first_step"),
    }


def rank_scenarios(user_profile: dict, scenarios: list) -> dict:
    """
    Рахує gaps/critical_areas один раз, викликає score_scenario для кожного
    сценарію, сортує за final_score (descending), формує фінальну
    структуру (top_recommendation, ranked_scenarios, critical_areas,
    model_note) за зразком розділу 15 документа.
    """
    computed_gaps = gaps_module.compute_gaps(user_profile)
    critical_areas = gaps_module.detect_critical_areas(user_profile)

    ranked_scenarios = [
        score_scenario(user_profile, scenario, computed_gaps, critical_areas)
        for scenario in scenarios
    ]
    ranked_scenarios.sort(key=lambda result: result["final_score"], reverse=True)

    top = ranked_scenarios[0] if ranked_scenarios else None
    top_recommendation = (
        {
            "scenario_id": top["scenario_id"],
            "name": top["name"],
            "final_score": top["final_score"],
            "risk_level": top["risk_level"],
        }
        if top
        else None
    )

    return {
        "top_recommendation": top_recommendation,
        "ranked_scenarios": ranked_scenarios,
        "critical_areas": critical_areas,
        "model_note": (
            "This model ranks scenarios by fit, feasibility, balance, and risk. "
            "It does not make the final decision."
        ),
    }
