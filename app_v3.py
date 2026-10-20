"""Isolated UI v3 entry point. The original dashboard remains app.py."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.claims import load_claims
from ui3.evidence import render_evidence
from ui3.home import render_home
from ui3.navigation import render_top_navigation
from ui3.patient import render_patient
from ui3.patients import render_patients


st.set_page_config(page_title="CycleTwin", layout="wide", initial_sidebar_state="collapsed")
st.markdown(f"<style>{Path('ui3/theme.css').read_text()}</style>", unsafe_allow_html=True)

claims = load_claims()
frozen_summary = claims["frozen_summary"]


def go_to(page: str) -> None:
    st.session_state["view"] = page


page, language = render_top_navigation()
if page == "Home":
    render_home(claims=claims, frozen_summary=frozen_summary, go_to=go_to, language=language)
elif page == "Synthetic patients":
    render_patients(language=language, go_to=go_to)
elif page == "One patient":
    render_patient(language=language, claims=claims)
elif page == "Evidence":
    render_evidence(claims=claims, language=language)
else:
    st.markdown(f"# {page}")
    st.markdown(
        "This screen will be redesigned in the next approved stage. The complete current dashboard remains available through `streamlit run app.py`."
    )
    st.markdown(
        '<aside class="ct-callout"><b>Synthetic research prototype.</b> Not for diagnosis, contraception, conception planning, or treatment decisions.</aside>',
        unsafe_allow_html=True,
    )
