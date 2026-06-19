"""Структури даних для профілю користувача та сценаріїв.

Тримаємо їх простими: dataclass-и серіалізуються в/з JSONB-поля `data`
у Supabase. Бізнес-логіки тут немає — лише форма даних і конвертація.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# Сфери життя для Balance Wheel (з дошки проєкту).
LIFE_DOMAINS = [
    "Здоров'я",
    "Навчання / розвиток",
    "Кар'єра / робота",
    "Стосунки",
    "Відпочинок / вільний час",
    "Сенс / впевненість",
]

# Варіанти фокусу.
FOCUS_AREAS = ["Кар'єра", "Навчання", "Гроші", "Баланс"]


@dataclass
class BalanceItem:
    """Оцінка однієї сфери: задоволеність і важливість 1–10."""

    domain: str
    satisfaction: int = 5
    importance: int = 5


@dataclass
class UserProfile:
    user_email: str
    balance_wheel: list[BalanceItem] = field(default_factory=list)
    focus_area: str = ""
    specific_request: str = ""
    # Додаткові фактори (Step 4 з анкети).
    available_hours_per_week: float = 0.0
    budget_level: str = ""  # low / medium / high
    current_energy: int = 5  # 1–10
    skill_level: str = ""  # beginner / intermediate / advanced
    motivation_level: int = 5  # 1–10
    has_first_step: bool = False
    support_level: str = ""  # none / some / strong

    def to_data(self) -> dict[str, Any]:
        """JSONB-payload (без user_email — він окрема колонка)."""
        d = asdict(self)
        d.pop("user_email", None)
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "UserProfile":
        data = row.get("data", {}) or {}
        balance = [BalanceItem(**b) for b in data.get("balance_wheel", [])]
        return cls(
            user_email=row["user_email"],
            balance_wheel=balance,
            focus_area=data.get("focus_area", ""),
            specific_request=data.get("specific_request", ""),
            available_hours_per_week=data.get("available_hours_per_week", 0.0),
            budget_level=data.get("budget_level", ""),
            current_energy=data.get("current_energy", 5),
            skill_level=data.get("skill_level", ""),
            motivation_level=data.get("motivation_level", 5),
            has_first_step=data.get("has_first_step", False),
            support_level=data.get("support_level", ""),
        )

    def to_prompt_text(self) -> str:
        """Людиночитний опис профілю для контексту LLM."""
        lines = [f"Email: {self.user_email}"]
        if self.balance_wheel:
            lines.append("Колесо балансу (задоволеність/важливість, 1–10):")
            for b in self.balance_wheel:
                lines.append(f"  - {b.domain}: {b.satisfaction}/{b.importance}")
        if self.focus_area:
            lines.append(f"Фокус: {self.focus_area}")
        if self.specific_request:
            lines.append(f"Конкретний запит: {self.specific_request}")
        lines.append(f"Доступно годин/тиждень: {self.available_hours_per_week}")
        lines.append(f"Бюджет: {self.budget_level or '—'}")
        lines.append(f"Поточна енергія (1–10): {self.current_energy}")
        lines.append(f"Рівень навичок: {self.skill_level or '—'}")
        lines.append(f"Мотивація (1–10): {self.motivation_level}")
        lines.append(f"Є перший крок: {'так' if self.has_first_step else 'ні'}")
        lines.append(f"Підтримка: {self.support_level or '—'}")
        return "\n".join(lines)


@dataclass
class Scenario:
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
            title=row["title"],
            goal_tags=data.get("goal_tags", []),
            requirements=data.get("requirements", ""),
            style=data.get("style", ""),
            risk=data.get("risk", ""),
        )

    def to_prompt_text(self) -> str:
        parts = [f"«{self.title}»"]
        if self.goal_tags:
            parts.append(f"теги: {', '.join(self.goal_tags)}")
        if self.requirements:
            parts.append(f"вимоги: {self.requirements}")
        if self.style:
            parts.append(f"стиль: {self.style}")
        if self.risk:
            parts.append(f"ризик: {self.risk}")
        return "; ".join(parts)
