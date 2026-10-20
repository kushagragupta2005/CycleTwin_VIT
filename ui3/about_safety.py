"""Safety, glossary, consent and local synthetic-import tools for v3."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import streamlit as st

from src.adapters.apple_health import parse_export, parse_upload_bytes
from src.safety import BOOLEAN_FIELDS, abstention_reasons


def _readable(name: str) -> str:
    return name.replace("_", " ")


def render_about_safety(*, claims: dict, language: str) -> None:
    detailed = language == "Detailed"
    safety_threshold = abstention_reasons.__defaults__[0]
    consented = bool(st.session_state.get("mock_consent", False))

    st.markdown('<span class="ct-badge">◌ Synthetic data only · safety and scope</span>', unsafe_allow_html=True)
    st.markdown("# About and safety")
    st.markdown("CycleTwin is a synthetic research prototype. This page explains the display’s boundaries, its explicit score-withholding rules, and the local import demonstration.")

    st.markdown("## What this demo is for")
    st.markdown(
        "**In plain words:** It demonstrates an engineering workflow for a generated late-or-absent-ovulation label. "
        "It does not diagnose PMOS, predict a person’s hormone levels, confirm ovulation, or support contraception, conception planning, or treatment decisions."
    )
    st.markdown(
        '<aside class="ct-callout"><b>Research boundary.</b> All records, labels, safety flags, and evaluation results are generated. '
        'The model has no clinical or external validation.</aside>', unsafe_allow_html=True,
    )

    st.markdown("## When the display withholds a score")
    st.markdown("**In plain words:** The display fails closed. If a rule fires, it shows the reason and withholds the score, interval, feature evidence, sandbox, and alert.")
    safety_groups = (
        ("Missing safety information", "A required declared safety value is missing or invalid."),
        ("Simulator flags", "Thyroid or prolactin reference flags, hormonal contraception, pregnancy-related states, and perimenopausal state."),
        ("Age-related condition", "An age below the declared gate or an early post-menarche condition."),
        ("Data completeness", f"Observed nightly temperature completeness below the configured {safety_threshold:.0%} threshold."),
    )
    cards = "".join(
        f'<article class="ct-card"><h3>{title}</h3><p>{body}</p></article>' for title, body in safety_groups
    )
    st.markdown(f'<div class="ct-grid ct-grid-4">{cards}</div>', unsafe_allow_html=True)
    with st.expander("Declared safety fields", expanded=detailed):
        st.markdown("The safety gate expects these explicit booleans: " + ", ".join(_readable(name) for name in BOOLEAN_FIELDS) + ".")
        st.caption("The dashboard maps generated archetypes to only the simulated flags required for the demonstration. It does not infer normal laboratory values from missing data.")

    st.markdown("## Consent receipt")
    if consented:
        st.success("Mock consent receipt recorded for this browser session · synthetic demo · no real data")
    else:
        st.info("No mock consent receipt is selected in this browser session. The acknowledgement control is on Home.")
    st.caption("The receipt is a UI acknowledgement for a synthetic demonstration. It does not collect consent or authorize processing of personal health data.")

    st.markdown("## Glossary")
    glossary = (
        ("PMOS", "A label used for synthetic generator archetypes. CycleTwin does not diagnose it."),
        ("Tier", "A selected set of synthetic input features for a saved fitted model."),
        ("Abstain", "Withhold a result because an explicit safety or completeness rule fired."),
        ("Conformal range", "A calibration-based output range. The generated ovulation-day range shown here failed its target coverage check."),
        ("Oracle-adjacent", "A simulator check that contains internal variables related to how the generated label was made; it is not real EHR fusion."),
    )
    for term, definition in glossary:
        with st.expander(term):
            st.write(definition)

    st.markdown("## Advanced tools")
    st.markdown("**In plain words:** This local parser reads a limited Apple Health-shaped XML schema only to test compatibility. It does not add an upload to the scored cohort or validate a clinical workflow.")
    with st.expander("Synthetic Apple Health import", expanded=False):
        st.caption("Use the bundled synthetic export only. The parser supports a limited subset of temperature, resting heart rate, HRV, step, sleep, and cycle-start records.")
        if st.button("Load synthetic Apple Health export", key="v3_apple_synthetic"):
            subprocess.run([sys.executable, "scripts/make_synthetic_apple_export.py"], check=True, capture_output=True)
            st.session_state["apple_loaded"] = True
        export_path = Path("apple_health_export/export.xml")
        if st.session_state.get("apple_loaded") and export_path.exists():
            parsed = parse_export(export_path)
            st.caption(f"Synthetic XML parsed: {len(parsed['daily'])} dates · {len(parsed['cycle_starts'])} cycle starts.")
        uploaded = st.file_uploader("Or upload a synthetic export XML", type=["xml"], key="v3_apple_upload")
        if uploaded:
            parsed = parse_upload_bytes(uploaded.getvalue())
            st.caption(f"Parsed {len(parsed['daily'])} dates · cycle starts: {len(parsed['cycle_starts'])}. The upload is not scored or added to the synthetic cohort.")

    st.markdown("## Read the project record")
    st.markdown(
        "- [Assumptions](docs/assumptions.md)\n"
        "- [Evaluation plan](docs/eval_plan.md)\n"
        "- [Research validity and related work](docs/related_work.md)\n"
        "- [Judge Q&A](docs/jury_qa.md)\n"
        "- [Privacy design notes](docs/privacy.md)"
    )
