"""Streamlit app: a 4-screen guided flow (landing -> profile -> chat -> results).

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import db
import llm
import decision_engine
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

st.set_page_config(page_title="AI Growth Advisor", layout="wide")

PAGES = ["landing", "profile", "chat", "results"]
STEP_LABELS = ["Test", "Profile", "Advisor", "Results"]


def humanize(value: str) -> str:
    """Turns 'save_money' into 'Save money' for display, while the
    underlying snake_case value is still what gets stored/scored."""
    if not value:
        return "Select an option"
    return value.replace("_", " ").capitalize()


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

        :root {
            --bg: #FFFFFF;
            --text: #16181D;
            --text-secondary: #6B7280;
            --accent: #F2C14E;
            --accent-dark: #E0AC2A;
            --accent-text: #1A1A2E;
            --card-blue-bg: #EAF4FB; --card-blue-line: #4F9FD8;
            --card-green-bg: #EAF8F1; --card-green-line: #45B383;
            --card-purple-bg: #F3EEFB; --card-purple-line: #9B7FE0;
            --border: #E7E8EC;
            --radius: 14px;
        }

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text); }
        h1, h2, h3, h4 { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; letter-spacing: -0.01em; }

        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding-top: 2.2rem; max-width: 1040px; }
        .landing-wrap { padding-top: 3rem; }

        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            padding: 0.55rem 1.4rem;
            border: 1px solid var(--border);
        }
        button[kind="primary"], [data-testid="stBaseButton-primary"], [data-testid="baseButton-primary"] {
            background-color: var(--accent) !important;
            color: var(--accent-text) !important;
            border: none !important;
        }
        button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
            background-color: var(--accent-dark) !important;
        }
        button[kind="secondary"], [data-testid="stBaseButton-secondary"] {
            background-color: white !important;
            color: var(--text) !important;
        }

        /* Sliders */
        .stSlider [data-baseweb="slider"] div[role="slider"] {
            background-color: var(--accent) !important;
            border-color: var(--accent) !important;
        }
        .stSlider [data-baseweb="slider"] > div > div {
            background: var(--accent) !important;
        }

        /* Step dots (clickable nav buttons) */
        .step-row-spacer { margin-bottom: 1.2rem; }
        div[class*="st-key-navstep_"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: var(--text-secondary) !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            padding: 0.25rem 0 !important;
        }
        div[class*="st-key-navstep_"] button:hover {
            color: var(--text) !important;
            background: transparent !important;
        }
        div[class*="st-key-navstep_"] { display: flex; justify-content: center; }

        /* Landing hero */
        .hero-title { text-align: center; font-size: 4.4rem; margin-bottom: 0.6rem; }
        .hero-subtitle { text-align: center; color: var(--text-secondary); font-size: 1.3rem; margin-bottom: 3.6rem; }

        .step-card { border-radius: var(--radius); padding: 2rem 1.8rem 2.2rem; height: 100%; min-height: 230px; border-top: 5px solid; }
        .step-card.blue { background: var(--card-blue-bg); border-color: var(--card-blue-line); }
        .step-card.green { background: var(--card-green-bg); border-color: var(--card-green-line); }
        .step-card.purple { background: var(--card-purple-bg); border-color: var(--card-purple-line); }
        .step-card .icon { margin-bottom: 1.3rem; }
        .step-card .icon svg { width: 46px; height: 46px; }
        .step-card .eyebrow { font-size: 0.82rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.45rem; }
        .step-card .title { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.4rem; line-height: 1.3; }

        /* Section labels */
        .section-label { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.05rem; margin: 1.6rem 0 0.6rem; }
        .field-caption { color: var(--text-secondary); font-size: 0.85rem; margin-top: -0.5rem; margin-bottom: 0.6rem; }

        /* Results */
        .result-hero { background: linear-gradient(135deg, var(--card-blue-bg), var(--card-green-bg)); border-radius: var(--radius); padding: 1.8rem 2rem; margin-bottom: 1.6rem; }
        .result-hero .label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-secondary); }
        .result-hero .name { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800; font-size: 1.7rem; margin: 0.2rem 0 0.5rem; }
        .result-hero .score { font-size: 1.1rem; font-weight: 700; }

        .scenario-card { border: 1px solid var(--border); border-radius: var(--radius); padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
        .scenario-card .top-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.7rem; }
        .scenario-card .name { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.1rem; }
        .scenario-card .score { font-weight: 700; color: var(--accent-dark); }

        .badge { display: inline-block; font-size: 0.72rem; font-weight: 600; padding: 0.18rem 0.6rem; border-radius: 999px; }
        .badge.low { background: #E5F6EC; color: #2E8B57; }
        .badge.medium { background: #FCF0DA; color: #B07B1F; }
        .badge.high { background: #FBE7E7; color: #C0392B; }

        .metric-row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.32rem; }
        .metric-row .metric-label { width: 110px; font-size: 0.78rem; color: var(--text-secondary); flex-shrink: 0; }
        .metric-track { flex-grow: 1; background: #F1F2F4; border-radius: 999px; height: 7px; overflow: hidden; }
        .metric-fill { height: 100%; border-radius: 999px; background: var(--accent-dark); }
        .metric-fill.risk { background: #D98989; }
        .metric-value { width: 34px; text-align: right; font-size: 0.78rem; color: var(--text-secondary); }

        .detail-line { font-size: 0.88rem; margin: 0.15rem 0; }
        .detail-line b { color: var(--text); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def step_indicator(current_page: str) -> None:
    idx = PAGES.index(current_page)
    st.markdown(
        f"<style>div[class~='st-key-navstep_{idx}'] button {{ "
        f"color: var(--accent-dark) !important; font-weight: 700 !important; }}</style>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(PAGES), gap="large")
    for i, (col, label) in enumerate(zip(cols, STEP_LABELS)):
        with col:
            with st.container(key=f"navstep_{i}"):
                dot = "\u25CF" if i == idx else "\u25CB"
                if st.button(f"{dot}  {label}", key=f"navbtn_{i}", use_container_width=False):
                    if i != idx:
                        go_to(PAGES[i])
    st.markdown('<div class="step-row-spacer"></div>', unsafe_allow_html=True)


def go_to(page: str) -> None:
    st.session_state["page"] = page
    st.rerun()


# ---------------------------------------------------------------------------
# Page 1: Landing
# ---------------------------------------------------------------------------
ICON_CHECKLIST = """
<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#4F9FD8" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M9 3.5h6v2.4H9z"/>
<path d="M8 11l1.8 1.8L14.5 9" /><path d="M8 16.2l1.8 1.8 4.7-4.8"/></svg>
"""
ICON_INSIGHT = """
<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#45B383" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
<rect x="4" y="14" width="3.6" height="6.5" rx="0.8"/><rect x="10.2" y="9" width="3.6" height="11.5" rx="0.8"/>
<rect x="16.4" y="4" width="3.6" height="16.5" rx="0.8"/></svg>
"""
ICON_UNLOCK = """
<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#9B7FE0" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="9" r="5.2"/><path d="M12 14v3.2"/><path d="M9 19.5l1.6-2.3h2.8L15 19.5"/>
<path d="M9.6 8.6l1.8 1.8 3-3.2"/></svg>
"""


def render_landing() -> None:
    st.markdown('<div class="hero-title">AI Growth Advisor</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Answer a short questionnaire and get a personalized, '
        'data-backed action plan.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(
            f'<div class="step-card blue"><div class="icon">{ICON_CHECKLIST}</div>'
            '<div class="eyebrow">Step 1</div><div class="title">Complete the Test</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="step-card green"><div class="icon">{ICON_INSIGHT}</div>'
            '<div class="eyebrow">Step 2</div><div class="title">View detailed scenarios suitable for you</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="step-card purple"><div class="icon">{ICON_UNLOCK}</div>'
            '<div class="eyebrow">Step 3</div><div class="title">Unlock Your Potential</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.write("")

    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if not st.session_state.get("show_email"):
            if st.button("Start the Test", type="primary", use_container_width=True):
                st.session_state["show_email"] = True
                st.rerun()
        else:
            with st.form("email_form", clear_on_submit=False):
                email = st.text_input(
                    "Email", placeholder="you@example.com", label_visibility="collapsed")
                go = st.form_submit_button(
                    "Continue", type="primary", use_container_width=True)
            if go:
                if email and "@" in email:
                    st.session_state["user_email"] = email
                    go_to("profile")
                else:
                    st.error("Please enter a valid email.")


# ---------------------------------------------------------------------------
# Page 2: Profile
# ---------------------------------------------------------------------------
def render_profile(user_email: str) -> None:
    step_indicator("profile")
    if st.button("\u2190 Back", type="secondary"):
        go_to("landing")

    st.markdown("## Your profile")
    st.caption(
        "This shapes which scenarios get recommended to you \u2014 take your time.")

    existing = db.load_profile(user_email)
    existing_by_domain = (
        {b.domain: b for b in existing.balance_wheel} if existing else {}
    )

    with st.form("profile_form"):
        st.markdown('<div class="section-label">Balance wheel</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="field-caption">For each area: how satisfied are you with it today, '
            'and how important is it to you.</div>',
            unsafe_allow_html=True,
        )
        balance: list[BalanceItem] = []
        for domain in BALANCE_DOMAINS:
            label = BALANCE_DOMAIN_LABELS.get(domain, domain)
            cur = existing_by_domain.get(domain)
            st.markdown(f"**{label}**")
            sat = st.slider("Satisfaction (1-10)", 1, 10,
                             cur.satisfaction if cur else 5, key=f"sat_{domain}")
            imp = st.slider("Importance (1-5)", 1, 5,
                             cur.importance if cur else 3, key=f"imp_{domain}")
            balance.append(BalanceItem(
                domain=domain, satisfaction=sat, importance=imp))
            st.write("")

        st.markdown('<div class="section-label">Your goal</div>',
                    unsafe_allow_html=True)
        focus = st.selectbox(
            "Focus area", FOCUS_AREAS,
            index=FOCUS_AREAS.index(existing.focus_area)
            if existing and existing.focus_area in FOCUS_AREAS else 0,
            format_func=humanize,
        )
        specific = st.selectbox(
            "Specific request", SPECIFIC_REQUESTS,
            index=SPECIFIC_REQUESTS.index(existing.specific_request)
            if existing and existing.specific_request in SPECIFIC_REQUESTS else 0,
            help="The most specific label for what you're trying to decide.",
            format_func=humanize,
        )
        free_text = st.text_area(
            "Tell us more, in your own words",
            value=existing.free_text_context if existing else "",
            placeholder="What exactly are you trying to solve or improve?",
        )

        st.markdown('<div class="section-label">Resources & capacity</div>',
                    unsafe_allow_html=True)
        hours = st.number_input(
            "Hours per week available", min_value=0.0, max_value=168.0,
            value=float(
                existing.available_hours_per_week) if existing else 0.0,
            step=1.0,
        )
        budget = st.selectbox(
            "Budget level", ["", *BUDGET_LEVELS],
            index=["", *BUDGET_LEVELS].index(existing.budget_level)
            if existing and existing.budget_level in ["", *BUDGET_LEVELS] else 0,
            format_func=humanize,
        )
        energy = st.slider(
            "Current energy (1-5)", 1, 5, existing.current_energy if existing else 3)
        skill = st.slider(
            "Current skill level (1-5)", 1, 5, existing.current_skill_level if existing else 3)

        st.markdown('<div class="section-label">Motivation & support</div>',
                    unsafe_allow_html=True)
        motivation = st.slider(
            "Motivation (1-5)", 1, 5, existing.motivation_level if existing else 3)
        autonomy = st.slider(
            "Autonomy (1-5)", 1, 5, existing.autonomy_level if existing else 3)
        support = st.slider(
            "Support available (1-5)", 1, 5, existing.support_level if existing else 3)

        st.markdown('<div class="section-label">Working style</div>',
                    unsafe_allow_html=True)
        preferred_format = st.selectbox(
            "Preferred action format", PREFERRED_ACTION_FORMATS,
            index=PREFERRED_ACTION_FORMATS.index(existing.preferred_action_format)
            if existing and existing.preferred_action_format in PREFERRED_ACTION_FORMATS else 0,
            format_func=humanize,
        )
        structure_need = st.slider(
            "Need for structure (1-5)", 1, 5, existing.structure_need if existing else 3)
        self_discipline = st.slider(
            "Self-discipline (1-5)", 1, 5, existing.self_discipline if existing else 3)
        social_energy = st.slider(
            "Social energy (1-5)", 1, 5, existing.social_energy if existing else 3)
        stress_tolerance = st.slider(
            "Stress tolerance (1-5)", 1, 5, existing.stress_tolerance if existing else 3)

        st.markdown('<div class="section-label">Risk attitude</div>',
                    unsafe_allow_html=True)
        perceived_reversibility = st.slider(
            "How reversible do changes usually feel to you? (1-5)", 1, 5,
            existing.perceived_reversibility if existing else 3,
        )
        user_uncertainty = st.slider(
            "Comfort with uncertainty (1 = very uncomfortable, 5 = very comfortable)", 1, 5,
            existing.user_uncertainty if existing else 3,
        )
        hidden_concerns = st.multiselect(
            "Any concerns weighing on you right now?",
            HIDDEN_CONCERNS,
            default=existing.hidden_concerns if existing else [],
            format_func=humanize,
        )

        _, btn_col = st.columns([4, 1])
        with btn_col:
            submitted = st.form_submit_button(
                "Save profile", type="primary", use_container_width=True)

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
            st.session_state["profile_saved"] = True
            st.success("Profile saved.")
        except Exception as e:
            st.session_state["profile_saved"] = False
            st.error(f"Could not save profile: {e}")

    if st.session_state.get("profile_saved"):
        _, cont_col = st.columns([4, 1])
        with cont_col:
            if st.button("Continue \u2192", type="primary", use_container_width=True, key="continue_to_chat"):
                go_to("chat")

    # --- Personal notes (optional, collapsed) ---
    with st.expander("Personal notes / options you're considering"):
        st.caption(
            "These are just personal notes \u2014 the scenarios actually scored "
            "in the simulation come from the shared scenario library."
        )
        try:
            scenarios = db.list_scenarios(user_email)
        except Exception as e:
            scenarios = []
            st.warning(f"Could not load notes: {e}")
        for s in scenarios:
            st.write("\u2022 " + s.to_prompt_text())

        with st.form("scenario_form", clear_on_submit=True):
            title = st.text_input("Title")
            tags = st.text_input("Tags (comma-separated)")
            reqs = st.text_area("Requirements")
            style = st.text_input("Style")
            risk = st.text_input("Risk")
            s_submit = st.form_submit_button("Add note")
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
                st.success("Note added.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not add note: {e}")


# ---------------------------------------------------------------------------
# Page 3: Chat advisor
# ---------------------------------------------------------------------------
def render_chat(user_email: str) -> None:
    step_indicator("chat")
    if st.button("\u2190 Edit profile", type="secondary"):
        go_to("profile")

    st.markdown("## Chat advisor")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if st.button("Run decision simulation", type="primary"):
        try:
            simulation = decision_engine.run_user_simulation_with_explanation(
                user_email)
            st.session_state["last_model_result"] = simulation["model_result"]
            st.session_state["last_explanation"] = simulation["explanation"]
            st.session_state["last_user_result_id"] = simulation["result_id"]
            go_to("results")
        except Exception as e:
            st.error(f"Simulation error: {e}")

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask about your growth or scenarios\u2026")
    if not prompt:
        return

    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

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


# ---------------------------------------------------------------------------
# Page 4: Results
# ---------------------------------------------------------------------------
METRIC_LABELS = {
    "goal_fit": "Goal fit",
    "balance_score": "Balance",
    "feasibility": "Feasibility",
    "readiness": "Readiness",
    "action_style_fit": "Style fit",
    "reversibility": "Reversibility",
}


def render_metric_bar(label: str, value: float, is_risk: bool = False) -> str:
    pct = round(max(0.0, min(1.0, value)) * 100)
    fill_class = "metric-fill risk" if is_risk else "metric-fill"
    return (
        f'<div class="metric-row"><div class="metric-label">{label}</div>'
        f'<div class="metric-track"><div class="{fill_class}" style="width:{pct}%"></div></div>'
        f'<div class="metric-value">{pct}%</div></div>'
    )


def render_results(user_email: str) -> None:
    step_indicator("results")
    if st.button("\u2190 Back to chat", type="secondary"):
        go_to("chat")

    result = st.session_state.get("last_model_result")
    explanation = st.session_state.get("last_explanation")

    if not result:
        st.info("Run a decision simulation from the Advisor tab to see results here.")
        return

    st.markdown("## Your results")

    top = result.get("top_recommendation")
    if top:
        risk = top.get("risk_level", "low")
        st.markdown(
            f'<div class="result-hero"><div class="label">Top recommendation</div>'
            f'<div class="name">{top.get("name", "\u2014")}</div>'
            f'<div class="score">{top.get("final_score", 0)}/100 '
            f'<span class="badge {risk}">{risk} risk</span></div></div>',
            unsafe_allow_html=True,
        )

    if explanation:
        st.markdown(explanation)

    st.markdown('<div class="section-label">All scored scenarios</div>',
                unsafe_allow_html=True)

    for item in result.get("ranked_scenarios", []):
        risk = item.get("risk_level", "low")
        breakdown = item.get("score_breakdown", {})
        bars_html = "".join(
            render_metric_bar(label, breakdown.get(key, 0))
            for key, label in METRIC_LABELS.items()
        )
        bars_html += render_metric_bar("Risk penalty",
                                        breakdown.get("risk_penalty", 0) / 0.15
                                        if breakdown.get("risk_penalty") else 0,
                                        is_risk=True)

        st.markdown(
            f'<div class="scenario-card">'
            f'<div class="top-row"><div class="name">{item.get("name", "\u2014")}</div>'
            f'<div class="score">{item.get("final_score", 0)}/100 '
            f'<span class="badge {risk}">{risk} risk</span></div></div>'
            f"{bars_html}"
            f'<div style="margin-top:0.7rem">'
            f'<div class="detail-line"><b>Main benefit:</b> {item.get("main_benefit", "\u2014")}</div>'
            f'<div class="detail-line"><b>Main cost:</b> {item.get("main_cost", "\u2014")}</div>'
            f'<div class="detail-line"><b>First step:</b> {item.get("first_step", "\u2014")}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        warnings = item.get("warnings", [])
        if warnings:
            with st.expander(f"Warnings for {item.get('name', '')}"):
                for w in warnings:
                    st.write("\u2022", w)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def main() -> None:
    inject_theme()

    if "page" not in st.session_state:
        st.session_state["page"] = "landing"

    page = st.session_state["page"]

    if page == "landing":
        render_landing()
        return

    user_email = st.session_state.get("user_email")
    if not user_email:
        go_to("landing")
        return

    if page == "profile":
        render_profile(user_email)
    elif page == "chat":
        render_chat(user_email)
    elif page == "results":
        render_results(user_email)
    else:
        go_to("landing")


if __name__ == "__main__":
    main()
