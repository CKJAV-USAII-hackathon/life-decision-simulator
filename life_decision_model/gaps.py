"""
gaps.py — розрахунок balance gaps і critical areas.

Gaps рахуються один раз на user_profile і не залежать від конкретного сценарію.
"""

from . import config


def _clamp(value: float, minimum: float = config.SCORE_MIN, maximum: float = config.SCORE_MAX) -> float:
    return max(minimum, min(maximum, float(value)))


def compute_gaps(user_profile: dict) -> dict:
    """
    Для кожної сфери balance wheel рахує gap:

        gap = (10 - satisfaction) / 9 × (importance / 5)

    Повертає {area_name: gap}, де gap обмежений у діапазоні 0..1.
    """
    balance = user_profile.get("balance", {})
    gaps = {}

    for area, values in balance.items():
        satisfaction = values.get("satisfaction", config.SATISFACTION_SCALE_MAX)
        importance = values.get("importance", 0)
        gap = (
            (config.SATISFACTION_SCALE_MAX - satisfaction)
            / (config.SATISFACTION_SCALE_MAX - 1)
            * (importance / config.IMPORTANCE_SCALE_MAX)
        )
        gaps[area] = _clamp(gap)

    return gaps


def detect_critical_areas(user_profile: dict) -> list:
    """
    Critical Area Rule:

        satisfaction <= 3 AND importance >= 4 -> critical area
    """
    balance = user_profile.get("balance", {})
    critical_areas = []

    for area, values in balance.items():
        satisfaction = values.get("satisfaction", config.SATISFACTION_SCALE_MAX)
        importance = values.get("importance", 0)
        if (
            satisfaction <= config.CRITICAL_AREA_SATISFACTION_MAX
            and importance >= config.CRITICAL_AREA_IMPORTANCE_MIN
        ):
            critical_areas.append(area)

    return critical_areas
