"""Synthetic-patient list for the isolated v3 interface."""
from __future__ import annotations

from html import escape

import numpy as np
import streamlit as st

from src.features import attach_prior_cycle_lengths
from src.generator import generate
from src.inference import predict
from src.safety import abstention_reasons, synthetic_safety_record


TIER_COPY = {
    0: "Cycle history only",
    1: "+ wearable signals",
    2: "+ nightly temperature · main result",
    3: "+ simulated health record · research check only",
}


@st.cache_data
def demo_cohort():
    return [row for row in attach_prior_cycle_lengths(generate(223, patients=36, cycles=2)) if row["cycle"] == 1]


def _status(row: dict) -> tuple[str, str, str]:
    if row["abstain"]:
        return "⏸", "Score withheld", "withheld"
    if row["flag"]:
        return "!", "Flagged for review", "flagged"
    return "○", "Not flagged", "neutral"


def _table(rows: list[dict], tier: int, detailed: bool) -> str:
    header = ("Patient", "Generated archetype", "Model score" if detailed else "Forecast result", "Information used", "Data complete", "Status")
    body = []
    for row in rows:
        icon, label, cls = _status(row)
        score = "Withheld" if row["abstain"] else f"{row['risk']:.3f}"
        score_text = score if detailed else ("Score held back" if row["abstain"] else f"{row['risk']:.0%}")
        percent = row["wear"] * 100
        cells = (
            row["patient"], row["phenotype"], score_text, f"Tier {tier}",
            f'<span class="ct-progress"><span style="width:{percent:.1f}%"></span></span> {percent:.0f}%',
            f'<span class="ct-status ct-status-{cls}">{icon} {escape(label)}</span>',
        )
        body.append("<tr>" + "".join(f'<td data-label="{escape(label)}">{cell}</td>' for label, cell in zip(header, cells)) + "</tr>")
    headings = "".join(f"<th>{escape(label)}</th>" for label in header)
    return f'<div class="ct-table-wrap"><table class="ct-table"><thead><tr>{headings}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def render_patients(*, language: str, go_to) -> None:
    detailed = language == "Detailed"
    st.markdown('<span class="ct-badge">◌ Synthetic data only · generated research records</span>', unsafe_allow_html=True)
    st.markdown("# Synthetic patients")
    st.markdown(
        "These are generated records, not people. Pick the information level and sort order to inspect how the research demo displays a score, a flag, or a withheld result."
    )
    tier = st.segmented_control(
        "Level of information", tuple(TIER_COPY), default=2, key="display_tier", format_func=lambda value: TIER_COPY[value],
        help="A model input set. Tier 3 is an oracle-adjacent simulator check, not real health-record data.",
    )
    if tier is None:
        tier = 2
    sort = st.segmented_control("Sort generated records", ("Risk", "Archetype", "Data completeness"), default="Risk", key="sort_by") or "Risk"
    records = demo_cohort()
    rows = []
    for record in records:
        flags = synthetic_safety_record(record, 14)
        reasons = abstention_reasons(flags)
        output = predict(record, 14, tier)
        rows.append({
            "patient": record["patient"], "phenotype": record["phenotype"], "risk": None if reasons else output["prob"],
            "abstain": bool(reasons), "flag": False if reasons else output["flag"], "reasons": reasons,
            "wear": float(np.isfinite(record["temperature"][:14]).mean()), "record": record,
        })
    sorters = {
        "Risk": lambda row: (row["abstain"], -(row["risk"] or 0), row["patient"]),
        "Archetype": lambda row: (row["phenotype"], row["patient"]),
        "Data completeness": lambda row: (-row["wear"], row["patient"]),
    }
    rows.sort(key=sorters[sort])
    st.markdown(
        '<p class="ct-inline-note"><b>Legend:</b> ○ Not flagged means the score stayed below its validation flag line. '
        '! Flagged for review means the synthetic score crossed that line. ⏸ Score withheld means a safety or completeness rule fired.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(_table(rows, tier, detailed), unsafe_allow_html=True)
    held_back = sum(row["abstain"] for row in rows)
    st.caption(f"Tier {tier} · forecast day 14 · generated display cohort only · {held_back}/{len(rows)} scores withheld by explicit demo rules.")
    selected = st.selectbox("Inspect one generated record", [row["patient"] for row in rows], key="patient_choice")
    st.session_state["selected_patient"] = selected
    st.button("Open this synthetic patient", on_click=go_to, args=("One patient",), type="primary")
