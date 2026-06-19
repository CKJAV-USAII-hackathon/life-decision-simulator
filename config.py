"""Читання секретів: спочатку st.secrets (Streamlit Cloud), потім .env / env.

Так один і той самий код працює і локально (.env), і в Streamlit Community
Cloud (Secrets UI), без змін.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # підвантажує .env локально; на хмарі просто нічого не робить


def get_secret(name: str, default: str | None = None) -> str | None:
    # st.secrets доступний лише всередині Streamlit-рантайму.
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name, default)
