"""Data structures for the user profile and scenarios.

These map 1:1 onto the JSON contract expected by the scoring engine in
`life_decision_model/schemas.py` (see USER_PROFILE_EXAMPLE / SCENARIO_EXAMPLE).
Keeping the dataclasses aligned with that schema means anything saved from
the Streamlit form can be scored without any extra translation layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# Life areas for the Balance Wheel. These keys are shared between the user
# profile ("balance") and every scenario's "impact" dict, so the scoring
# model can match them up.
BALANCE_DOMAINS = ["career", "money", "learning", "relationships", "health", "hobby"]

BALANCE_DOMAIN_LABELS = {
    "career": "Career / work",
    "money": "Money / finances",
    "learning": "Learning / growth",
    "relationships": "Relationships",
    "health": "Health",
    "hobby": "Free time / hobbies",
}

# Controlled vocabulary so user answers line up with scenario tags.
FOCUS_AREAS = ["career", "money", "learning", "relationships", "health", "balance"]

SPECIFIC_REQUESTS = [
    "increase_income",
    "change_career",
    "find_new_job",
    "start_business",
    "save_money",
    "learn_new_skill",
    "get_certification",
    "improve_relationship",
    "build_new_relationships",
    "improve_health",
    "build_habit",
    "reduce_stress",
    "find_balance",
    "build_confidence",
    "other",
]

BUDGET_LEVELS = ["low", "medium", "high"]

PREFERRED_ACTION_FORMATS = ["clear_structure", "flexible", "routine", "creative", "social"]

HIDDEN_CONCERNS = [
    "overload",
    "lack_of_time_for_family",
    "financial_risk",
    "burnout",
    "uncertainty",
    "low_energy_and_low_free_time",
    "social_pressure",
    "fear_of_failure",
]


@dataclass
class BalanceItem:
    """One life-area rating: satisfaction (1-10) and importance (1-5)."""

    domain: str
    satisfaction: int = 5
    importance: int = 3


@dataclass
class UserProfile:
    user_email: str

    focus_area: str = ""
    specific_request: str = ""
    explicit_options: list[str] = field(default_factory=list)
    free_text_context: str = ""

    balance_wheel: list[BalanceItem] = field(default_factory=list)

    available_hours_per_week: float = 0.0
    budget_level: str = ""  # low / medium / high
    current_energy: int = 3  # 1-5
    current_skill_level: int = 3  # 1-5

    motivation_level: int = 3  # 1-5
    autonomy_level: int = 3  # 1-5
    support_level: int = 3  # 1-5

    preferred_action_format: str = ""
    structure_need: int = 3  # 1-5
    self_discipline: int = 3  # 1-5
    social_energy: int = 3  # 1-5
    stress_tolerance: int = 3  # 1-5

    perceived_reversibility: int = 3  # 1-5
    user_uncertainty: int = 3  # 1-5

    hidden_concerns: list[str] = field(default_factory=list)

    # ---- conversion to/from the scoring-model JSON contract ----

    def to_data(self) -> dict[str, Any]:
        """JSONB payload in the exact shape the scoring engine expects."""
        balance = {
            b.domain: {"satisfaction": b.satisfaction, "importance": b.importance}
            for b in self.balance_wheel
        }
        return {
            "user_id": self.user_email,
            "focus_area": self.focus_area,
            "specific_request": self.specific_request,
            "explicit_options": self.explicit_options,
            "free_text_context": self.free_text_context,
            "balance": balance,
            "available_hours_per_week": self.available_hours_per_week,
            "budget_level": self.budget_level,
            "current_energy": self.current_energy,
            "current_skill_level": self.current_skill_level,
            "motivation_level": self.motivation_level,
            "autonomy_level": self.autonomy_level,
            "support_level": self.support_level,
            "preferred_action_format": self.preferred_action_format,
            "structure_need": self.structure_need,
            "self_discipline": self.self_discipline,
            "social_energy": self.social_energy,
            "stress_tolerance": self.stress_tolerance,
            "perceived_reversibility": self.perceived_reversibility,
            "user_uncertainty": self.user_uncertainty,
            "hidden_concerns": self.hidden_concerns,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "UserProfile":
        data = row.get("data", {}) or {}
        balance_raw = data.get("balance", {}) or {}
        balance = [
            BalanceItem(
                domain=domain,
                satisfaction=values.get("satisfaction", 5),
                importance=values.get("importance", 3),
            )
            for domain, values in balance_raw.items()
        ]
        return cls(
            user_email=row.get("user_email", data.get("user_id", "")),
            focus_area=data.get("focus_area", ""),
            specific_request=data.get("specific_request", ""),
            explicit_options=data.get("explicit_options", []),
            free_text_context=data.get("free_text_context", ""),
            balance_wheel=balance,
            available_hours_per_week=data.get("available_hours_per_week", 0.0),
            budget_level=data.get("budget_level", ""),
            current_energy=data.get("current_energy", 3),
            current_skill_level=data.get("current_skill_level", 3),
            motivation_level=data.get("motivation_level", 3),
            autonomy_level=data.get("autonomy_level", 3),
            support_level=data.get("support_level", 3),
            preferred_action_format=data.get("preferred_action_format", ""),
            structure_need=data.get("structure_need", 3),
            self_discipline=data.get("self_discipline", 3),
            social_energy=data.get("social_energy", 3),
            stress_tolerance=data.get("stress_tolerance", 3),
            perceived_reversibility=data.get("perceived_reversibility", 3),
            user_uncertainty=data.get("user_uncertainty", 3),
            hidden_concerns=data.get("hidden_concerns", []),
        )

    def to_prompt_text(self) -> str:
        """Human-readable profile summary used as LLM chat context."""
        lines = [f"User: {self.user_email}"]
        if self.balance_wheel:
            lines.append("Balance wheel (satisfaction 1-10 / importance 1-5):")
            for b in self.balance_wheel:
                label = BALANCE_DOMAIN_LABELS.get(b.domain, b.domain)
                lines.append(f"  - {label}: {b.satisfaction}/{b.importance}")
        if self.focus_area:
            lines.append(f"Focus area: {self.focus_area}")
        if self.specific_request:
            lines.append(f"Specific request: {self.specific_request}")
        if self.free_text_context:
            lines.append(f"In their own words: {self.free_text_context}")
        lines.append(f"Available hours/week: {self.available_hours_per_week}")
        lines.append(f"Budget level: {self.budget_level or '—'}")
        lines.append(f"Current energy (1-5): {self.current_energy}")
        lines.append(f"Current skill level (1-5): {self.current_skill_level}")
        lines.append(f"Motivation (1-5): {self.motivation_level}")
        lines.append(f"Autonomy (1-5): {self.autonomy_level}")
        lines.append(f"Support available (1-5): {self.support_level}")
        lines.append(f"Preferred action format: {self.preferred_action_format or '—'}")
        if self.hidden_concerns:
            lines.append(f"Hidden concerns: {', '.join(self.hidden_concerns)}")
        return "\n".join(lines)


@dataclass
class Scenario:
    """Free-form scenario, as captured from the simple sidebar form.

    Note: this short shape is NOT enough for the scoring engine (which
    needs the full contract from life_decision_model/schemas.py). It's kept
    only so users can jot down personal notes/options in the UI; the actual
    ranked scenarios used by "Run decision simulation" are the ones loaded
    from `seed_scenarios.py` (see db.list_model_scenarios_data).
    """

    user_email: str
    title: str
    goal_tags: list[str] = field(default_factory=list)
    requirements: str = ""
    style: str = ""
    risk: str = ""

    def to_data(self) -> dict[str, Any]:
        return {
            "goal_tags": self.goal_tags,
            "requirements": self.requirements,
            "style": self.style,
            "risk": self.risk,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Scenario":
        data = row.get("data", {}) or {}
        return cls(
            user_email=row["user_email"],
            title=row.get("title", data.get("name", "")),
            goal_tags=data.get("goal_tags", []),
            requirements=data.get("requirements", ""),
            style=data.get("style", ""),
            risk=data.get("risk", ""),
        )

    def to_prompt_text(self) -> str:
        parts = [f"\u201c{self.title}\u201d"]
        if self.goal_tags:
            parts.append(f"tags: {', '.join(self.goal_tags)}")
        if self.requirements:
            parts.append(f"requirements: {self.requirements}")
        if self.style:
            parts.append(f"style: {self.style}")
        if self.risk:
            parts.append(f"risk: {self.risk}")
        return "; ".join(parts)
