"""
config.py — усі числові константи для deterministic scoring model.

Формули відповідають оновленій методичці Life Decision Simulator:
Goal Fit, Balance Score, Feasibility, Readiness, Action Style Fit,
Reversibility Score та Risk Penalty.
"""

# ---------------------------------------------------------------------------
# Загальні межі score
# ---------------------------------------------------------------------------
SCORE_MIN = 0.0
SCORE_MAX = 1.0

# ---------------------------------------------------------------------------
# Фінальна scoring formula
# ---------------------------------------------------------------------------
FINAL_SCORE_WEIGHTS = {
    "goal_fit": 0.20,
    "balance_score": 0.25,
    "feasibility": 0.20,
    "action_style_fit": 0.15,
    "readiness": 0.15,
    "reversibility": 0.05,
}
# Risk Penalty не входить у словник — він віднімається окремо.

# ---------------------------------------------------------------------------
# Goal Fit
# ---------------------------------------------------------------------------
GOAL_FIT_SPECIFIC_REQUEST_MATCH = 1.0
GOAL_FIT_FOCUS_AREA_MATCH = 0.7
GOAL_FIT_CATEGORY_MATCH = 0.5
GOAL_FIT_NO_MATCH = 0.2
GOAL_FIT_EXPLICIT_OPTION_BOOST = 0.9

# ---------------------------------------------------------------------------
# Balance Score
# ---------------------------------------------------------------------------
IMPACT_SCALE_MAX = 5
NEUTRAL_BALANCE_SCORE = 0.5

# ---------------------------------------------------------------------------
# Feasibility
# ---------------------------------------------------------------------------
FEASIBILITY_WEIGHTS = {
    "time_fit": 0.35,
    "budget_fit": 0.25,
    "energy_fit": 0.25,
    "skill_fit": 0.15,
}
ENERGY_FIT_MAX_GAP = 4

BUDGET_FIT_TABLE = {
    ("low", "low"): 1.0,
    ("low", "medium"): 0.5,
    ("low", "high"): 0.1,
    ("medium", "low"): 1.0,
    ("medium", "medium"): 1.0,
    ("medium", "high"): 0.5,
    ("high", "low"): 1.0,
    ("high", "medium"): 1.0,
    ("high", "high"): 1.0,
}
DEFAULT_BUDGET_FIT = 1.0

# ---------------------------------------------------------------------------
# Readiness, COM-B model
# ---------------------------------------------------------------------------
READINESS_WEIGHTS = {
    "capability": 0.33,
    "opportunity": 0.33,
    "motivation": 0.34,
}
SCALE_1_5_MAX = 5

# ---------------------------------------------------------------------------
# Action Style Fit
# ---------------------------------------------------------------------------
ACTION_STYLE_WEIGHTS = {
    "format_fit": 0.30,
    "structure_fit": 0.25,
    "discipline_fit": 0.20,
    "social_fit": 0.15,
    "pace_fit": 0.10,
}
FORMAT_FIT_MATCH = 1.0
FORMAT_FIT_NO_MATCH = 0.5
STYLE_MAX_GAP = 4
INDEPENDENCE_BASE = 6  # independence_demand = 6 - structure_level

# ---------------------------------------------------------------------------
# Reversibility Score
# ---------------------------------------------------------------------------
REVERSIBILITY_MAX = 5

# ---------------------------------------------------------------------------
# Balance Wheel / Critical Area Rule
# ---------------------------------------------------------------------------
CRITICAL_AREA_SATISFACTION_MAX = 3
CRITICAL_AREA_IMPORTANCE_MIN = 4
SATISFACTION_SCALE_MAX = 10
IMPORTANCE_SCALE_MAX = 5

# ---------------------------------------------------------------------------
# Risk Penalty
# ---------------------------------------------------------------------------
RISK_PENALTY_WEIGHTS = {
    "critical_area_harm": 0.07,
    "overload_risk": 0.05,
    "uncertainty_risk": 0.03,
}
RISK_PENALTY_CAP = 0.15

OVERLOAD_ENERGY_LOW_MAX = 2
OVERLOAD_FREE_TIME_SATISFACTION_MAX = 3
OVERLOAD_FREE_TIME_IMPORTANCE_MIN = 4
OVERLOAD_INTENSITY_HIGH_MIN = 4
OVERLOAD_SIGNAL_COUNT = 4
FREE_TIME_AREA_KEY = "hobby"

UNCERTAINTY_LEVEL_HIGH_MIN = 4
UNCERTAINTY_REVERSIBILITY_LOW_MAX = 2
UNCERTAINTY_SIGNAL_COUNT = 2

# ---------------------------------------------------------------------------
# risk_level — інтерпретація risk_penalty для UI / warnings
# ---------------------------------------------------------------------------
RISK_LEVEL_LOW_MAX = 0.05
RISK_LEVEL_MEDIUM_MAX = 0.10
