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

MODEL = "gemini-2.5-flash"  # switch to gemini-2.5-pro if needed

SYSTEM_BASE = (
    "You are a personal development and decision-making advisor. "
    "You rely on the user's profile (balance wheel, focus area, resources, "
    "motivation) and their scenarios.\n"
    "Response rules:\n"
    "- Reply in English, short and to the point: 2-4 sentences or up to 4 bullet points.\n"
    "- Stay strictly on topic. No intros, no repeating the question, no disclaimers, no filler.\n"
    "- Be concrete: give one or two realistic first steps.\n"
    "- If you're missing information, ask EXACTLY one short clarifying question.\n"
    "- Don't go outside the topic of personal development, decisions, and the user's profile."
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
        parts.append("\n--- User profile ---\n" +
                     profile.to_prompt_text())
    else:
        parts.append("\n(Profile not filled in yet.)")
    if scenarios:
        parts.append("\n--- User's notes ---")
        for s in scenarios:
            parts.append("\u2022 " + s.to_prompt_text())
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
    Explains the scoring model result in plain language.
    The LLM does NOT change the ranking and does NOT invent new scores.
    """
    system = (
        "You are the result explainer for the Life Decision Simulator. "
        "You do NOT change the scenario ranking and do NOT invent new scores. "
        "You receive the structured output of the scoring model and explain it "
        "in plain English. "
        "Show the top 3 scenarios, their scores, why they fit, the main "
        "trade-off, and the first practical step. "
        "Don't print the full score breakdown, since detailed scores are "
        "shown separately. "
        "Write like a product-quality chat reply, with no technical jargon."
    )

    prompt = {
        "profile": profile_data,
        "model_result": model_result,
        "instruction": (
            "Explain the top-3 scenarios to the user. "
            "Response format:\n"
            "1. A short conclusion: which option is best and why.\n"
            "2. Top-3 scenarios: name, score /100, brief explanation.\n"
            "3. For each: main benefit, main trade-off or risk, first step.\n"
            "4. End by noting this is a trade-off simulation, not a final decision made for the user."
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
