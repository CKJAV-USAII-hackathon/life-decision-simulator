"""
metrics.py — формули метрик для deterministic balance-aware scoring model.

Реалізовані метрики:
- Goal Fit
- Balance Score
- Feasibility
- Readiness
- Action Style Fit
- Reversibility Score
- Risk Penalty

Усі метрики повертають значення у діапазоні 0..1, якщо не зазначено інше.
"""

from __future__ import annotations

from . import config


def clamp(value: float, minimum: float = config.SCORE_MIN, maximum: float = config.SCORE_MAX) -> float:
    """Обмежує числове значення заданими межами."""
    return max(minimum, min(maximum, float(value)))


def _as_list(value) -> list:
    """Повертає value як list, щоб коректно обробляти None/string/list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# =============================================================================
# Goal Fit
# =============================================================================
def compute_goal_fit(user_profile: dict, scenario: dict) -> float:
    """
    Рахує відповідність сценарію запиту користувача.

    Rule-based формула для MVP:
        if specific_request in best_for_requests: Goal Fit = 1.0
        elif focus_area in goal_tags:             Goal Fit = 0.7
        elif focus_area == category:              Goal Fit = 0.5
        else:                                     Goal Fit = 0.2

    Додатково:
        if scenario_id in explicit_options: Goal Fit = max(Goal Fit, 0.9)
    """
    focus_area = user_profile.get("focus_area")
    specific_request = user_profile.get("specific_request")
    explicit_options = set(_as_list(user_profile.get("explicit_options")))

    goal_tags = set(_as_list(scenario.get("goal_tags")))
    best_for_requests = set(_as_list(scenario.get("best_for_requests")))
    category = scenario.get("category")
    scenario_id = scenario.get("scenario_id")

    if specific_request and specific_request in best_for_requests:
        score = config.GOAL_FIT_SPECIFIC_REQUEST_MATCH
    elif focus_area and focus_area in goal_tags:
        score = config.GOAL_FIT_FOCUS_AREA_MATCH
    elif focus_area and category and focus_area == category:
        score = config.GOAL_FIT_CATEGORY_MATCH
    else:
        score = config.GOAL_FIT_NO_MATCH

    if scenario_id and scenario_id in explicit_options:
        score = max(score, config.GOAL_FIT_EXPLICIT_OPTION_BOOST)

    return clamp(score)


# =============================================================================
# Balance Score
# =============================================================================
def compute_balance_score(
    user_profile: dict,
    scenario: dict,
    gaps: dict,
    critical_areas: list,
) -> float:
    """
    Рахує, як сценарій впливає на важливі й слабкі сфери життя.

    Для кожної сфери:
        area_weight = gap
        impact_norm = impact / 5

    Потім:
        balance_effect = sum(area_weight * impact_norm) / sum(area_weight)
        balance_score = (balance_effect + 1) / 2

    Якщо sum(area_weight) = 0, повертається нейтральне значення 0.5.
    """
    del user_profile, critical_areas  # потрібні для спільної сигнатури, але не для формули

    impact = scenario.get("impact", {})
    total_weight = sum(max(0.0, float(gap)) for gap in gaps.values())

    if total_weight <= 0:
        return config.NEUTRAL_BALANCE_SCORE

    weighted_effect = 0.0
    for area, gap in gaps.items():
        area_weight = max(0.0, float(gap))
        impact_norm = clamp(
            float(impact.get(area, 0)) / config.IMPACT_SCALE_MAX,
            -1.0,
            1.0,
        )
        weighted_effect += area_weight * impact_norm

    balance_effect = weighted_effect / total_weight
    balance_score = (balance_effect + 1.0) / 2.0
    return clamp(balance_score)


# =============================================================================
# Feasibility
# =============================================================================
def time_fit(available_hours_per_week: float, scenario_time_required_per_week: float) -> float:
    """time_fit = min(1, available_hours / required_hours)."""
    if scenario_time_required_per_week <= 0:
        return 1.0
    return clamp(available_hours_per_week / scenario_time_required_per_week)


def budget_fit(user_budget_level: str, scenario_budget_required: str) -> float:
    """Budget Fit за таблицею відповідності budget-рівнів."""
    return clamp(
        config.BUDGET_FIT_TABLE.get(
            (user_budget_level, scenario_budget_required),
            config.DEFAULT_BUDGET_FIT,
        )
    )


def energy_fit(scenario_intensity: float, user_energy: float) -> float:
    """energy_fit = 1 - max(0, scenario_intensity - user_energy) / 4."""
    score = 1.0 - max(0.0, scenario_intensity - user_energy) / config.ENERGY_FIT_MAX_GAP
    return clamp(score)


def skill_fit(user_skill_level: float, scenario_skill_required: float) -> float:
    """skill_fit = min(1, user_skill_level / scenario_skill_required)."""
    if scenario_skill_required <= 0:
        return 1.0
    return clamp(user_skill_level / scenario_skill_required)


def compute_feasibility(user_profile: dict, scenario: dict) -> float:
    """
    Feasibility =
        0.35 × Time Fit + 0.25 × Budget Fit + 0.25 × Energy Fit + 0.15 × Skill Fit
    """
    t = time_fit(
        user_profile.get("available_hours_per_week", 0),
        scenario.get("time_required_per_week", 0),
    )
    b = budget_fit(
        user_profile.get("budget_level", "low"),
        scenario.get("budget_required", "low"),
    )
    e = energy_fit(
        scenario.get("intensity", 1),
        user_profile.get("current_energy", 5),
    )
    s = skill_fit(
        user_profile.get("current_skill_level", 0),
        scenario.get("skill_required", 0),
    )

    w = config.FEASIBILITY_WEIGHTS
    return clamp(
        w["time_fit"] * t
        + w["budget_fit"] * b
        + w["energy_fit"] * e
        + w["skill_fit"] * s
    )


# =============================================================================
# Readiness
# =============================================================================
def compute_readiness(user_profile: dict, scenario: dict) -> float:
    """
    Readiness = 0.33 × Capability + 0.33 × Opportunity + 0.34 × Motivation

    Де:
        Capability  = skill_fit
        Opportunity = average(time_fit, budget_fit, support)
        Motivation  = average(motivation, autonomy)
    """
    capability = skill_fit(
        user_profile.get("current_skill_level", 0),
        scenario.get("skill_required", 0),
    )

    t = time_fit(
        user_profile.get("available_hours_per_week", 0),
        scenario.get("time_required_per_week", 0),
    )
    b = budget_fit(
        user_profile.get("budget_level", "low"),
        scenario.get("budget_required", "low"),
    )
    support = clamp(user_profile.get("support_level", 0) / config.SCALE_1_5_MAX)
    opportunity = (t + b + support) / 3.0

    motivation_norm = clamp(user_profile.get("motivation_level", 0) / config.SCALE_1_5_MAX)
    autonomy_norm = clamp(user_profile.get("autonomy_level", 0) / config.SCALE_1_5_MAX)
    motivation = (motivation_norm + autonomy_norm) / 2.0

    w = config.READINESS_WEIGHTS
    return clamp(
        w["capability"] * capability
        + w["opportunity"] * opportunity
        + w["motivation"] * motivation
    )


# =============================================================================
# Action Style Fit
# =============================================================================
def format_fit(preferred_action_format: str, preferred_formats: list) -> float:
    """Format Fit = 1.0, якщо preferred_action_format підтримується сценарієм, інакше 0.5."""
    return config.FORMAT_FIT_MATCH if preferred_action_format in preferred_formats else config.FORMAT_FIT_NO_MATCH


def structure_fit(structure_need: float, structure_level: float) -> float:
    """Structure Fit = 1 - abs(structure_need - structure_level) / 4."""
    return clamp(1.0 - abs(structure_need - structure_level) / config.STYLE_MAX_GAP)


def discipline_fit(self_discipline: float, structure_level: float) -> float:
    """
    independence_demand = 6 - structure_level
    Discipline Fit = 1 - max(0, independence_demand - self_discipline) / 4
    """
    independence_demand = config.INDEPENDENCE_BASE - structure_level
    score = 1.0 - max(0.0, independence_demand - self_discipline) / config.STYLE_MAX_GAP
    return clamp(score)


def social_fit(social_energy: float, social_intensity: float) -> float:
    """Social Fit = 1 - max(0, social_intensity - social_energy) / 4."""
    score = 1.0 - max(0.0, social_intensity - social_energy) / config.STYLE_MAX_GAP
    return clamp(score)


def pace_fit(stress_tolerance: float, intensity: float) -> float:
    """Pace Fit = 1 - max(0, intensity - stress_tolerance) / 4."""
    score = 1.0 - max(0.0, intensity - stress_tolerance) / config.STYLE_MAX_GAP
    return clamp(score)


def compute_action_style_fit(user_profile: dict, scenario: dict) -> float:
    """
    Action Style Fit =
        0.30 × Format Fit
        + 0.25 × Structure Fit
        + 0.20 × Discipline Fit
        + 0.15 × Social Fit
        + 0.10 × Pace Fit
    """
    preferred_formats = _as_list(scenario.get("preferred_formats"))

    fmt = format_fit(user_profile.get("preferred_action_format"), preferred_formats)
    struct = structure_fit(
        user_profile.get("structure_need", 3),
        scenario.get("structure_level", 3),
    )
    discipline = discipline_fit(
        user_profile.get("self_discipline", 3),
        scenario.get("structure_level", 3),
    )
    social = social_fit(
        user_profile.get("social_energy", 3),
        scenario.get("social_intensity", 3),
    )
    pace = pace_fit(
        user_profile.get("stress_tolerance", 3),
        scenario.get("intensity", 3),
    )

    w = config.ACTION_STYLE_WEIGHTS
    return clamp(
        w["format_fit"] * fmt
        + w["structure_fit"] * struct
        + w["discipline_fit"] * discipline
        + w["social_fit"] * social
        + w["pace_fit"] * pace
    )


# =============================================================================
# Reversibility
# =============================================================================
def compute_reversibility_score(scenario: dict) -> float:
    """reversibility_score = scenario_reversibility / 5."""
    return clamp(scenario.get("reversibility", 0) / config.REVERSIBILITY_MAX)


# =============================================================================
# Risk Penalty
# =============================================================================
def critical_area_harm(scenario: dict, critical_areas: list) -> float:
    """Critical Area Harm = частка critical areas, які сценарій погіршує."""
    if not critical_areas:
        return 0.0
    impact = scenario.get("impact", {})
    harmed = sum(1 for area in critical_areas if impact.get(area, 0) < 0)
    return clamp(harmed / len(critical_areas))


def overload_risk(user_profile: dict, scenario: dict) -> float:
    """
    Overload Risk = кількість сигналів перевантаження / 4:
        current_energy <= 2
        free_time/hobby critical
        intensity >= 4
        time_required_per_week > available_hours_per_week
    """
    signals = 0

    if user_profile.get("current_energy", 5) <= config.OVERLOAD_ENERGY_LOW_MAX:
        signals += 1

    hobby = user_profile.get("balance", {}).get(config.FREE_TIME_AREA_KEY, {})
    if (
        hobby.get("satisfaction", config.SATISFACTION_SCALE_MAX)
        <= config.OVERLOAD_FREE_TIME_SATISFACTION_MAX
        and hobby.get("importance", 0) >= config.OVERLOAD_FREE_TIME_IMPORTANCE_MIN
    ):
        signals += 1

    if scenario.get("intensity", 0) >= config.OVERLOAD_INTENSITY_HIGH_MIN:
        signals += 1

    if scenario.get("time_required_per_week", 0) > user_profile.get("available_hours_per_week", 0):
        signals += 1

    return clamp(signals / config.OVERLOAD_SIGNAL_COUNT)


def uncertainty_risk(scenario: dict) -> float:
    """Uncertainty Risk = кількість сигналів невизначеності / 2."""
    signals = 0

    if scenario.get("uncertainty_level", 0) >= config.UNCERTAINTY_LEVEL_HIGH_MIN:
        signals += 1

    if scenario.get("reversibility", config.REVERSIBILITY_MAX) <= config.UNCERTAINTY_REVERSIBILITY_LOW_MAX:
        signals += 1

    return clamp(signals / config.UNCERTAINTY_SIGNAL_COUNT)


def compute_risk_penalty(user_profile: dict, scenario: dict, critical_areas: list) -> float:
    """
    Risk Penalty =
        0.07 × Critical Area Harm
        + 0.05 × Overload Risk
        + 0.03 × Uncertainty Risk
    з верхнім обмеженням 0.15.
    """
    harm = critical_area_harm(scenario, critical_areas)
    overload = overload_risk(user_profile, scenario)
    uncertainty = uncertainty_risk(scenario)

    w = config.RISK_PENALTY_WEIGHTS
    penalty = (
        w["critical_area_harm"] * harm
        + w["overload_risk"] * overload
        + w["uncertainty_risk"] * uncertainty
    )
    return clamp(min(penalty, config.RISK_PENALTY_CAP))
