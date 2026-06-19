"""Обгортка над Google Gemini.

Формує system prompt із профілю користувача та його сценаріїв, тримає
розмову й повертає відповідь моделі.
"""

from __future__ import annotations

from functools import lru_cache

from google import genai
from google.genai import types

from config import get_secret
from models import Scenario, UserProfile
import json

MODEL = "gemini-2.5-flash"  # за потреби заміни на gemini-2.5-pro

SYSTEM_BASE = (
    "Ти — консультант з особистого розвитку та прийняття рішень. "
    "Спираєшся на профіль користувача (колесо балансу, фокус, ресурси, мотивацію) "
    "і його сценарії.\n"
    "Правила відповіді:\n"
    "- Відповідай українською, коротко й чітко: 2–4 речення або до 4 пунктів.\n"
    "- Лише по суті запиту. Без вступів, повторів питання, дисклеймерів і води.\n"
    "- Давай конкретику: один-два реалістичні перші кроки.\n"
    "- Якщо бракує даних — постав РІВНО одне коротке уточнювальне питання.\n"
    "- Не виходь за тему особистого розвитку, рішень і профілю користувача."
)


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    key = get_secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "Не задано GEMINI_API_KEY. Додай у .env або st.secrets.")
    return genai.Client(api_key=key)


def build_system_prompt(
    profile: UserProfile | None, scenarios: list[Scenario]
) -> str:
    parts = [SYSTEM_BASE]
    if profile:
        parts.append("\n--- Профіль користувача ---\n" +
                     profile.to_prompt_text())
    else:
        parts.append("\n(Профіль ще не заповнений.)")
    if scenarios:
        parts.append("\n--- Сценарії користувача ---")
        for s in scenarios:
            parts.append("• " + s.to_prompt_text())
    return "\n".join(parts)


def chat(
    history: list[dict],
    profile: UserProfile | None,
    scenarios: list[Scenario],
) -> str:
    """history — список {'role': 'user'|'assistant', 'content': str}."""
    system = build_system_prompt(profile, scenarios)

    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )

    response = _client().models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.4,
            max_output_tokens=400,
            # Вимикаємо «мислення», щоб бюджет токенів ішов на саму відповідь
            # і вона не обрізалася.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    return response.text or ""


def explain_model_result(model_result: dict, profile_data: dict | None = None) -> str:
    """
    Пояснює результат scoring model людською мовою.
    LLM не змінює ranking і не вигадує нові бали.
    """
    system = (
        "Ти — пояснювач результатів Life Decision Simulator. "
        "Ти НЕ змінюєш ranking сценаріїв і НЕ вигадуєш нові бали. "
        "Ти отримуєш structured output scoring model і пояснюєш його простою українською мовою. "
        "Покажи 3 найкращі сценарії, їхні бали, чому вони підходять, основний trade-off "
        "і перший практичний крок. "
        "Не виводь повний score breakdown, бо детальні бали будуть доступні окремо. "
        "Пиши як продуктова відповідь у чаті, без технічного жаргону."
    )

    prompt = {
        "profile": profile_data,
        "model_result": model_result,
        "instruction": (
            "Поясни користувачу top-3 сценарії. "
            "Формат відповіді:\n"
            "1. Короткий висновок: який варіант найкращий і чому.\n"
            "2. Top-3 сценарії: назва, score /100, коротке пояснення.\n"
            "3. Для кожного: головна користь, головний trade-off або ризик, перший крок.\n"
            "4. Наприкінці зазнач, що це симуляція trade-offs, а не остаточне рішення за користувача."
        ),
    }

    response = _client().models.generate_content(
        model=MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=json.dumps(prompt, ensure_ascii=False, indent=2)
                    )
                ],
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.3,
            max_output_tokens=1000,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )

    return response.text or ""
