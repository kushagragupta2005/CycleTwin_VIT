"""Navigation wrapper for the isolated v3 interface."""
from __future__ import annotations

import streamlit as st


PAGES = ("Home", "Synthetic patients", "One patient", "Evidence", "Meet Kushi", "About and safety")


def render_top_navigation() -> tuple[str, str]:
    """Keep the established view key while using one mobile-scrollable control."""
    with st.container(key="ct_topbar"):
        left, right = st.columns([4, 1], vertical_alignment="center")
        with left:
            st.markdown('<div class="ct-brand">CycleTwin</div>', unsafe_allow_html=True)
        with right:
            language = st.segmented_control(
                "Language level", ("Simple", "Detailed"), default="Simple", key="language_level",
                label_visibility="collapsed",
            ) or "Simple"
    page = st.segmented_control("Navigate", PAGES, default="Home", key="view", label_visibility="collapsed") or "Home"
    return page, language
