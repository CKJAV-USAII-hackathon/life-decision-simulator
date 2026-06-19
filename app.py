"""Streamlit-додаток: анкета профілю + чат-консультант на Gemini.

Запуск:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import db
import llm
from models import (
    FOCUS_AREAS,
    LIFE_DOMAINS,
    BalanceItem,
    Scenario,
    UserProfile,
)

import decision_engine

st.set_page_config(page_title="AI-консультант розвитку", page_icon="🧭")


# ----- Ідентифікація користувача (поки що просто email) -----
def get_user_email() -> str | None:
    with st.sidebar:
        st.header("Користувач")
        email = st.text_input(
            "Email", value=st.session_state.get("user_email", ""))
        if email:
            st.session_state["user_email"] = email
        return email or None


def profile_tab(user_email: str) -> None:
    st.subheader("Профіль")

    existing = db.load_profile(user_email)

    with st.form("profile_form"):
        st.markdown("**Колесо балансу** (задоволеність / важливість, 1–10)")
        balance: list[BalanceItem] = []
        existing_by_domain = (
            {b.domain: b for b in existing.balance_wheel} if existing else {}
        )
        for domain in LIFE_DOMAINS:
            cur = existing_by_domain.get(domain)
            c1, c2 = st.columns(2)
            sat = c1.slider(
                f"{domain} — задоволеність", 1, 10,
                cur.satisfaction if cur else 5, key=f"sat_{domain}",
            )
            imp = c2.slider(
                f"{domain} — важливість", 1, 10,
                cur.importance if cur else 5, key=f"imp_{domain}",
            )
            balance.append(BalanceItem(
                domain=domain, satisfaction=sat, importance=imp))

        focus = st.selectbox(
            "Фокус", FOCUS_AREAS,
            index=FOCUS_AREAS.index(existing.focus_area)
            if existing and existing.focus_area in FOCUS_AREAS else 0,
        )
        specific = st.text_area(
            "Конкретний запит",
            value=existing.specific_request if existing else "",
            placeholder="Що саме хочеш вирішити або покращити?",
        )

        st.markdown("**Додаткові фактори**")
        c1, c2 = st.columns(2)
        hours = c1.number_input(
            "Годин/тиждень",
            min_value=0.0,
            max_value=168.0,
            value=float(
                existing.available_hours_per_week) if existing else 0.0,
            step=1.0,
        )
        budget = c2.selectbox(
            "Бюджет", ["", "low", "medium", "high"],
            index=["", "low", "medium", "high"].index(existing.budget_level)
            if existing and existing.budget_level in ["", "low", "medium", "high"] else 0,
        )
        c3, c4 = st.columns(2)
        energy = c3.slider(
            "Поточна енергія", 1, 10, existing.current_energy if existing else 5,
        )
        motivation = c4.slider(
            "Мотивація", 1, 10, existing.motivation_level if existing else 5,
        )
        c5, c6 = st.columns(2)
        skill = c5.selectbox(
            "Рівень навичок", ["", "beginner", "intermediate", "advanced"],
            index=["", "beginner", "intermediate",
                   "advanced"].index(existing.skill_level)
            if existing and existing.skill_level in ["", "beginner", "intermediate", "advanced"] else 0,
        )
        support = c6.selectbox(
            "Підтримка", ["", "none", "some", "strong"],
            index=["", "none", "some", "strong"].index(existing.support_level)
            if existing and existing.support_level in ["", "none", "some", "strong"] else 0,
        )
        has_step = st.checkbox(
            "Уже є перший крок", value=existing.has_first_step if existing else False
        )

        submitted = st.form_submit_button("Зберегти профіль")

    if submitted:
        profile = UserProfile(
            user_email=user_email,
            balance_wheel=balance,
            focus_area=focus,
            specific_request=specific,
            available_hours_per_week=hours,
            budget_level=budget,
            current_energy=energy,
            skill_level=skill,
            motivation_level=motivation,
            has_first_step=has_step,
            support_level=support,
        )
        try:
            db.save_profile(profile)
            st.success("Профіль збережено ✅")
        except Exception as e:
            st.error(f"Не вдалося зберегти: {e}")

    # --- Сценарії ---
    st.divider()
    st.markdown("**Сценарії**")
    scenarios = []
    try:
        scenarios = db.list_scenarios(user_email)
    except Exception as e:
        st.warning(f"Не вдалося завантажити сценарії: {e}")
    for s in scenarios:
        st.write("• " + s.to_prompt_text())

    with st.expander("Додати сценарій"):
        with st.form("scenario_form", clear_on_submit=True):
            title = st.text_input("Назва сценарію")
            tags = st.text_input("Теги цілі (через кому)")
            reqs = st.text_area("Вимоги")
            style = st.text_input("Стиль")
            risk = st.text_input("Ризик")
            s_submit = st.form_submit_button("Додати")
        if s_submit and title:
            try:
                db.save_scenario(Scenario(
                    user_email=user_email,
                    title=title,
                    goal_tags=[t.strip()
                               for t in tags.split(",") if t.strip()],
                    requirements=reqs,
                    style=style,
                    risk=risk,
                ))
                st.success("Сценарій додано ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Не вдалося додати: {e}")


def chat_tab(user_email: str) -> None:
    st.subheader("Чат-консультант")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if st.button("🧭 Запустити симуляцію рішення"):
        st.session_state["messages"].append({
            "role": "user",
            "content": "Запусти симуляцію рішення."
        })

        try:
            simulation = decision_engine.run_user_simulation_with_explanation(
                user_email)

            reply = simulation["explanation"]

            st.session_state["last_model_result"] = simulation["model_result"]
            st.session_state["last_user_result_id"] = simulation["result_id"]

        except Exception as e:
            reply = f"Помилка симуляції: {e}"

        st.session_state["messages"].append({
            "role": "assistant",
            "content": reply
        })

        st.rerun()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if "last_model_result" in st.session_state:
        with st.expander("ℹ️ Подивитися детальні бали останньої симуляції"):
            result = st.session_state["last_model_result"]

            top = result.get("top_recommendation", {})
            if top:
                st.markdown("**Top recommendation**")
                st.json(top)

            st.markdown("**Score breakdown by scenario**")

            for item in result.get("ranked_scenarios", []):
                st.markdown(
                    f"### {item.get('name', '—')} — {item.get('final_score', 0)}/100"
                )

                st.json(item.get("score_breakdown", {}))

                warnings = item.get("warnings", [])
                if warnings:
                    st.markdown("**Warnings:**")
                    for warning in warnings:
                        st.write("•", warning)

    prompt = st.chat_input("Запитай про свій розвиток або сценарії…")
    if not prompt:
        return

    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Контекст: профіль + сценарії з БД.
    try:
        profile = db.load_profile(user_email)
        scenarios = db.list_scenarios(user_email)
    except Exception as e:
        profile, scenarios = None, []
        st.warning(f"Контекст із БД недоступний: {e}")

    with st.chat_message("assistant"):
        with st.spinner("Думаю…"):
            try:
                reply = llm.chat(
                    st.session_state["messages"], profile, scenarios)
            except Exception as e:
                reply = f"Помилка LLM: {e}"
            st.markdown(reply)

    st.session_state["messages"].append(
        {"role": "assistant", "content": reply})


def main() -> None:
    st.title("🧭 AI-консультант розвитку")
    user_email = get_user_email()
    if not user_email:
        st.info("Введи email у боковій панелі, щоб почати.")
        return

    tab_profile, tab_chat = st.tabs(["Профіль", "Чат"])
    with tab_profile:
        profile_tab(user_email)
    with tab_chat:
        chat_tab(user_email)


if __name__ == "__main__":
    main()
