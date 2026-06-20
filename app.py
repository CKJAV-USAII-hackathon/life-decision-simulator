"""Streamlit app: profile questionnaire + Gemini-powered chat advisor.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import db
import llm
from models import (
    BALANCE_DOMAINS,
    BALANCE_DOMAIN_LABELS,
    BUDGET_LEVELS,
    FOCUS_AREAS,
    HIDDEN_CONCERNS,
    PREFERRED_ACTION_FORMATS,
    SPECIFIC_REQUESTS,
    BalanceItem,
    Scenario,
    UserProfile,
)

import decision_engine

st.set_page_config(page_title="AI Growth Advisor", page_icon="\U0001F9ED")


# ----- User identification (email is used as the user id for now) -----
def get_user_email() -> str | None:
    with st.sidebar:
        st.header("User")
        email = st.text_input(
            "Email", value=st.session_state.get("user_email", ""))
        if email:
            st.session_state["user_email"] = email
        return email or None


def profile_tab(user_email: str) -> None:
    st.subheader("Profile")

    existing = db.load_profile(user_email)

    with st.form("profile_form"):
        st.markdown("**Balance wheel** (satisfaction 1-10 / importance 1-5)")
        balance: list[BalanceItem] = []
        existing_by_domain = (
            {b.domain: b for b in existing.balance_wheel} if existing else {}
        )
        for domain in BALANCE_DOMAINS:
            label = BALANCE_DOMAIN_LABELS.get(domain, domain)
            cur = existing_by_domain.get(domain)
            c1, c2 = st.columns(2)
            sat = c1.slider(
                f"{label} \u2014 satisfaction", 1, 10,
                cur.satisfaction if cur else 5, key=f"sat_{domain}",
            )
            imp = c2.slider(
                f"{label} \u2014 importance", 1, 5,
                cur.importance if cur else 3, key=f"imp_{domain}",
            )
            balance.append(BalanceItem(
                domain=domain, satisfaction=sat, importance=imp))

        focus = st.selectbox(
            "Focus area", FOCUS_AREAS,
            index=FOCUS_AREAS.index(existing.focus_area)
            if existing and existing.focus_area in FOCUS_AREAS else 0,
        )
        specific = st.selectbox(
            "Specific request", SPECIFIC_REQUESTS,
            index=SPECIFIC_REQUESTS.index(existing.specific_request)
            if existing and existing.specific_request in SPECIFIC_REQUESTS else 0,
            help="The most specific label for what you're trying to decide. "
                 "Used to match you with the best-fitting scenarios.",
        )
        free_text = st.text_area(
            "Tell us more, in your own words",
            value=existing.free_text_context if existing else "",
            placeholder="What exactly are you trying to solve or improve?",
        )

        st.markdown("**Resources & capacity**")
        c1, c2 = st.columns(2)
        hours = c1.number_input(
            "Hours/week available",
            min_value=0.0,
            max_value=168.0,
            value=float(
                existing.available_hours_per_week) if existing else 0.0,
            step=1.0,
        )
        budget = c2.selectbox(
            "Budget level", ["", *BUDGET_LEVELS],
            index=["", *BUDGET_LEVELS].index(existing.budget_level)
            if existing and existing.budget_level in ["", *BUDGET_LEVELS] else 0,
        )
        c3, c4 = st.columns(2)
        energy = c3.slider(
            "Current energy (1-5)", 1, 5,
            existing.current_energy if existing else 3,
        )
        skill = c4.slider(
            "Current skill level (1-5)", 1, 5,
            existing.current_skill_level if existing else 3,
        )

        st.markdown("**Motivation & support**")
        c5, c6, c7 = st.columns(3)
        motivation = c5.slider(
            "Motivation (1-5)", 1, 5,
            existing.motivation_level if existing else 3,
        )
        autonomy = c6.slider(
            "Autonomy (1-5)", 1, 5,
            existing.autonomy_level if existing else 3,
        )
        support = c7.slider(
            "Support available (1-5)", 1, 5,
            existing.support_level if existing else 3,
        )

        st.markdown("**Working style**")
        preferred_format = st.selectbox(
            "Preferred action format", PREFERRED_ACTION_FORMATS,
            index=PREFERRED_ACTION_FORMATS.index(existing.preferred_action_format)
            if existing and existing.preferred_action_format in PREFERRED_ACTION_FORMATS else 0,
        )
        c8, c9, c10 = st.columns(3)
        structure_need = c8.slider(
            "Need for structure (1-5)", 1, 5,
            existing.structure_need if existing else 3,
        )
        self_discipline = c9.slider(
            "Self-discipline (1-5)", 1, 5,
            existing.self_discipline if existing else 3,
        )
        social_energy = c10.slider(
            "Social energy (1-5)", 1, 5,
            existing.social_energy if existing else 3,
        )
        stress_tolerance = st.slider(
            "Stress tolerance (1-5)", 1, 5,
            existing.stress_tolerance if existing else 3,
        )

        st.markdown("**Risk attitude**")
        c11, c12 = st.columns(2)
        perceived_reversibility = c11.slider(
            "How reversible do changes usually feel to you? (1-5)", 1, 5,
            existing.perceived_reversibility if existing else 3,
        )
        user_uncertainty = c12.slider(
            "How comfortable are you with uncertainty? (1 = very uncomfortable, 5 = very comfortable)",
            1, 5,
            existing.user_uncertainty if existing else 3,
        )
        hidden_concerns = st.multiselect(
            "Any concerns weighing on you right now?",
            HIDDEN_CONCERNS,
            default=existing.hidden_concerns if existing else [],
        )

        submitted = st.form_submit_button("Save profile")

    if submitted:
        profile = UserProfile(
            user_email=user_email,
            focus_area=focus,
            specific_request=specific,
            explicit_options=existing.explicit_options if existing else [],
            free_text_context=free_text,
            balance_wheel=balance,
            available_hours_per_week=hours,
            budget_level=budget,
            current_energy=energy,
            current_skill_level=skill,
            motivation_level=motivation,
            autonomy_level=autonomy,
            support_level=support,
            preferred_action_format=preferred_format,
            structure_need=structure_need,
            self_discipline=self_discipline,
            social_energy=social_energy,
            stress_tolerance=stress_tolerance,
            perceived_reversibility=perceived_reversibility,
            user_uncertainty=user_uncertainty,
            hidden_concerns=hidden_concerns,
        )
        try:
            db.save_profile(profile)
            st.success("Profile saved \u2705")
        except Exception as e:
            st.error(f"Could not save profile: {e}")

    # --- Personal notes / scenarios ---
    st.divider()
    st.markdown("**Your notes / options you're considering**")
    st.caption(
        "These are just personal notes \u2014 the scenarios actually scored "
        "in the simulation come from the shared scenario library."
    )
    scenarios = []
    try:
        scenarios = db.list_scenarios(user_email)
    except Exception as e:
        st.warning(f"Could not load notes: {e}")
    for s in scenarios:
        st.write("\u2022 " + s.to_prompt_text())

    with st.expander("Add a note"):
        with st.form("scenario_form", clear_on_submit=True):
            title = st.text_input("Title")
            tags = st.text_input("Tags (comma-separated)")
            reqs = st.text_area("Requirements")
            style = st.text_input("Style")
            risk = st.text_input("Risk")
            s_submit = st.form_submit_button("Add")
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
                st.success("Note added \u2705")
                st.rerun()
            except Exception as e:
                st.error(f"Could not add note: {e}")


def chat_tab(user_email: str) -> None:
    st.subheader("Chat advisor")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if st.button("\U0001F9ED Run decision simulation"):
        st.session_state["messages"].append({
            "role": "user",
            "content": "Run a decision simulation."
        })

        try:
            simulation = decision_engine.run_user_simulation_with_explanation(
                user_email)

            reply = simulation["explanation"]

            st.session_state["last_model_result"] = simulation["model_result"]
            st.session_state["last_user_result_id"] = simulation["result_id"]

        except Exception as e:
            reply = f"Simulation error: {e}"

        st.session_state["messages"].append({
            "role": "assistant",
            "content": reply
        })

        st.rerun()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if "last_model_result" in st.session_state:
        with st.expander("\u2139\uFE0F See detailed scores from the last simulation"):
            result = st.session_state["last_model_result"]

            top = result.get("top_recommendation", {})
            if top:
                st.markdown("**Top recommendation**")
                st.json(top)

            st.markdown("**Score breakdown by scenario**")

            for item in result.get("ranked_scenarios", []):
                st.markdown(
                    f"### {item.get('name', '\u2014')} \u2014 {item.get('final_score', 0)}/100"
                )

                st.json(item.get("score_breakdown", {}))

                warnings = item.get("warnings", [])
                if warnings:
                    st.markdown("**Warnings:**")
                    for warning in warnings:
                        st.write("\u2022", warning)

    prompt = st.chat_input("Ask about your growth or scenarios\u2026")
    if not prompt:
        return

    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Context: profile + notes from the DB.
    try:
        profile = db.load_profile(user_email)
        scenarios = db.list_scenarios(user_email)
    except Exception as e:
        profile, scenarios = None, []
        st.warning(f"Could not load context from the database: {e}")

    with st.chat_message("assistant"):
        with st.spinner("Thinking\u2026"):
            try:
                reply = llm.chat(
                    st.session_state["messages"], profile, scenarios)
            except Exception as e:
                reply = f"LLM error: {e}"
            st.markdown(reply)

    st.session_state["messages"].append(
        {"role": "assistant", "content": reply})


def main() -> None:
    st.title("\U0001F9ED AI Growth Advisor")
    user_email = get_user_email()
    if not user_email:
        st.info("Enter your email in the sidebar to get started.")
        return

    tab_profile, tab_chat = st.tabs(["Profile", "Chat"])
    with tab_profile:
        profile_tab(user_email)
    with tab_chat:
        chat_tab(user_email)


if __name__ == "__main__":
    main()
