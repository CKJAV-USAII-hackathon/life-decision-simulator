"""
schemas.py — очікувана структура `user_profile.json` і `scenarios.json`.

# формат погоджений робочий, але ще не остаточний

Це довідковий файл (розділ 4 архітектурного документа: "ні від чого не
залежить"). Він нічого не імпортує і не валідує — лише фіксує контракт,
який scoring model очікує отримати від анкети/LLM Parser (user_profile) і
від Scenario Library (scenarios), за прикладами з розділів 7–8
project_model_summary_with_formulas.md.

REQUIRED_*_FIELDS_FOR_SCORING — поля, без яких не порахуються метрики, що
мають готову формулу (Goal Fit, Balance Score, Feasibility, Readiness,
Action Style Fit, Reversibility, Risk Penalty, gaps, critical areas). Це не строгий валідатор, лише список для довідки —
якщо захочеться додати реальну валідацію пізніше, можна побудувати її саме
на цих списках.
"""

# -----------------------------------------------------------------------
# user_profile.json
# -----------------------------------------------------------------------
USER_PROFILE_EXAMPLE = {
    "user_id": "user_001",
    "focus_area": "money",
    "specific_request": "increase_income",
    "explicit_options": ["second_job", "salary_negotiation_cv"],
    "free_text_context": (
        "I want to increase my income but have low energy and "
        "almost no time for family."
    ),

    # balance wheel: satisfaction 1..10, importance 1..5 (розділ 7)
    "balance": {
        "career": {"satisfaction": 5, "importance": 5},
        "learning": {"satisfaction": 6, "importance": 3},
        "money": {"satisfaction": 3, "importance": 5},
        "relationships": {"satisfaction": 2, "importance": 5},
        "hobby": {"satisfaction": 3, "importance": 4},
    },

    "available_hours_per_week": 5,
    "budget_level": "low",        # "low" | "medium" | "high"
    "current_energy": 2,          # 1..5
    "current_skill_level": 3,     # 1..5

    "motivation_level": 4,        # 1..5
    "autonomy_level": 4,          # 1..5
    "support_level": 3,           # 1..5

    "preferred_action_format": "clear_structure",
    "structure_need": 5,          # 1..5
    "self_discipline": 3,         # 1..5
    "social_energy": 2,           # 1..5
    "stress_tolerance": 2,        # 1..5

    # для MVP базова формула Reversibility використовує scenario.reversibility,
    # ці два поля поки що лише додатковий сигнал для explanation/warning
    # (розділ 21.3 документа)
    "perceived_reversibility": 3,  # 1..5
    "user_uncertainty": 4,         # 1..5

    "hidden_concerns": ["overload", "lack_of_time_for_family"],
}

REQUIRED_USER_PROFILE_FIELDS_FOR_SCORING = [
    "focus_area",
    "specific_request",
    "explicit_options",
    "balance",
    "available_hours_per_week",
    "budget_level",
    "current_energy",
    "current_skill_level",
    "motivation_level",
    "autonomy_level",
    "support_level",
    "preferred_action_format",
    "structure_need",
    "self_discipline",
    "social_energy",
    "stress_tolerance",
]


# -----------------------------------------------------------------------
# один елемент scenarios.json
# -----------------------------------------------------------------------
SCENARIO_EXAMPLE = {
    "scenario_id": "second_job",
    "name": "Take a second job",
    "category": "income",
    "goal_tags": ["money", "increase_income"],
    "best_for_requests": ["increase_income_fast"],

    "time_required_per_week": 12,
    "budget_required": "low",     # "low" | "medium" | "high"
    "skill_required": 2,          # 1..5, 0 = навичка не потрібна
    "intensity": 5,                # 1..5

    "preferred_formats": ["clear_structure", "routine"],
    "structure_level": 4,         # 1..5
    "social_intensity": 3,        # 1..5
    "feedback_level": 2,          # 1..5

    # вплив на сфери balance wheel + energy, шкала приблизно -5..5
    "impact": {
        "career": 1,
        "learning": 0,
        "money": 5,
        "relationships": -3,
        "hobby": -5,
        "energy": -4,
    },

    "reversibility": 4,            # 1..5
    "uncertainty_level": 2,        # 1..5
    "risk_tags": ["overload", "less_time_for_relationships"],
    "not_recommended_if": ["low_energy_and_low_free_time"],

    "main_benefit": "Fastest income increase",
    "main_cost": "High cost for energy, relationships, and free time",
    "tradeoffs": [
        "Improves money quickly",
        "Can increase overload",
        "Reduces free time",
    ],
    "first_step": "Estimate weekly schedule and check whether 12 extra hours are realistic.",
}

REQUIRED_SCENARIO_FIELDS_FOR_SCORING = [
    "scenario_id",
    "name",
    "category",
    "goal_tags",
    "best_for_requests",
    "time_required_per_week",
    "budget_required",
    "skill_required",
    "intensity",
    "preferred_formats",
    "structure_level",
    "social_intensity",
    "impact",
    "reversibility",
    "uncertainty_level",
]
