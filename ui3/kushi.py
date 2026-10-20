"""Fictional Kushi scenario for the isolated v3 interface."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.inference import safe_predict
from src.personas import make_kushi
from src.safety import synthetic_safety_record
from src.uncertainty import uncertainty


def _signals(record: dict, day: int) -> pd.DataFrame:
    return pd.DataFrame({
        "Cycle day": np.arange(1, day + 1), "Temperature offset (°C)": record["temperature"][:day],
        "RHR offset (synthetic units)": record["rhr"][:day], "HRV offset (synthetic units)": record["hrv"][:day],
        "Sleep (hours)": record["sleep"][:day], "Steps": record["steps"][:day],
    }).set_index("Cycle day")


def _scenario_output(record: dict, day: int, tier: int, flags: dict) -> dict:
    return safe_predict(record, day, tier, safety=flags)


def _forecast_panel(record: dict, day: int, tier: int, flags: dict, claims: dict) -> None:
    output = _scenario_output(record, day, tier, flags)
    if output["abstain"]:
        st.markdown(
            '<section class="ct-abstain"><b>⏸ Score withheld · guardrail active</b><br>Rule fired: '
            + "; ".join(output["reasons"]) + "</section>",
            unsafe_allow_html=True,
        )
        st.markdown("**In plain words:** A guardrail removes the score, interval, feature evidence, sandbox, and alert when this fictional scenario is unsuitable for the display.")
        return
    interval = uncertainty(record, day, tier, output)
    score, range_card, status = st.columns(3)
    with score:
        st.metric("Fitted synthetic forecast score", f"{output['prob']:.0%}", help="Score for the generated late-or-absent-ovulation label; not a diagnosis probability.")
    with range_card:
        st.metric("Illustrative day range", f"{interval['interval'][0]}–{interval['interval'][1]}", help="A synthetic calibration illustration, not an individual guarantee.")
    with status:
        label = "! Flagged for review" if output["flag"] else "○ Not flagged"
        style = "flagged" if output["flag"] else "neutral"
        st.markdown(f'<span class="ct-status ct-status-{style}">{label}</span>', unsafe_allow_html=True)
        st.caption(f"Validation threshold: {output['threshold']:.3f}")
    target = 1 - float(claims["conformal"]["protocol"]["alpha"])
    st.caption(
        f"Tier {tier} · forecast day {day} · generated scenario only. The day range did not meet its {target:.0%} frozen coverage target and must not be used as a timing guarantee."
    )


def render_kushi(*, claims: dict, language: str) -> None:
    detailed = language == "Detailed"
    persona = make_kushi()
    profile = claims["kushi"]["profile"]
    cycles = persona["cycles"]
    days = tuple(claims["configuration"]["days"])
    tiers = tuple(claims["configuration"]["tiers"])

    st.markdown('<span class="ct-badge">◌ Synthetic data only · fictional scenario</span>', unsafe_allow_html=True)
    st.markdown("# Meet Kushi")
    st.markdown("Kushi is a fictional, generated scenario for walking through the research interface. Her story is not a real person, a patient record, or performance evidence.")

    st.markdown("## A fictional scenario")
    identity, story = st.columns([1, 1.7])
    with identity:
        st.markdown(
            f'<article class="ct-card"><h3>{profile["name"]}</h3><div class="ct-card-number ct-card-number-small">{profile["age"]}</div>'
            f'<p>years old · year {profile["study_year"]} {profile["course"]}</p></article>',
            unsafe_allow_html=True,
        )
    with story:
        st.markdown(f"**Scenario context:** {profile['story']}")
        st.markdown("**In plain words:** This narrative is only a way to navigate synthetic screens. It does not represent a woman with PMOS or predict an individual outcome.")
        st.caption(persona["scenario_disclosure"])

    st.markdown("## Generated history")
    st.markdown("**In plain words:** These are the generated lengths used for the fictional backstory. They are not measurements from a person.")
    st.dataframe(pd.DataFrame({"Past generated cycle": range(1, len(persona["six_past_lengths"]) + 1), "Length (days)": persona["six_past_lengths"]}), hide_index=True, use_container_width=True)
    with st.expander("How this fictional example was selected", expanded=detailed):
        st.write(persona["selection_rule"])
        st.caption("The selection rule does not consult a model score. Profile age, BMI, and family-history values are declared fictional overrides.")

    st.markdown("## Walk through one generated scenario")
    chosen_cycle = st.segmented_control("Generated scenario cycle", tuple(item["logical_cycle"] for item in cycles), default=cycles[0]["logical_cycle"], key="kushi_cycle_v3")
    if chosen_cycle is None:
        chosen_cycle = cycles[0]["logical_cycle"]
    scenario = next(item for item in cycles if item["logical_cycle"] == chosen_cycle)
    record = scenario["record"]
    controls = st.columns(2)
    with controls[0]:
        tier = st.segmented_control("Information tier", tiers, default=2, key="kushi_tier_v3", format_func=lambda value: f"Tier {value}") or 2
    with controls[1]:
        day = st.segmented_control("Forecast day", days, default=days[len(days) // 2], key="kushi_day_v3", format_func=lambda value: f"Day {value}") or days[len(days) // 2]
    st.caption(f"Generated scenario seed {scenario['seed']} · scenario cycle {scenario['logical_cycle']} · requested Tier {tier} · data through day {day}.")

    st.markdown("### Two generated data streams")
    st.markdown("**In plain words:** The model can use prior-cycle history and wearable-style values available by this selected day. It does not use measured hormones.")
    observations = _signals(record, day)
    st.line_chart(observations[["Temperature offset (°C)"]])
    st.caption(f"{observations['Temperature offset (°C)'].notna().sum()} of {len(observations)} generated nightly temperatures are present; missing nights remain missing.")
    with st.expander("Advanced study details", expanded=detailed):
        st.dataframe(observations, use_container_width=True)
        st.dataframe(pd.DataFrame([{
            "Age": record["age"], "BMI": record["bmi"], "Family history": record["family_history"],
            "Simulator IR latent": record["ir"], "Simulator androgen": record["androgen"],
        }]), hide_index=True, use_container_width=True)
        st.caption("The static values are simulator internals, not real EHR records, clinical laboratory results, or hormone measurements. Tier 3 is an oracle-adjacent research check.")

    st.markdown("### The fitted research display")
    st.markdown("**In plain words:** This computes a score for the simulator’s late-or-absent-ovulation label using the saved fitted model and explicit safety gate.")
    flags = synthetic_safety_record(record, day)
    _forecast_panel(record, day, tier, flags, claims)

    st.markdown("## Guardrails live")
    st.markdown("**In plain words:** Turn on a fictional condition to see the rule withhold the score. These controls do not diagnose Kushi or change a real person’s care.")
    guardrails = st.columns(3)
    with guardrails[0]: contraception = st.checkbox("Fictional hormonal contraception", key="kushi_contraception_v3")
    with guardrails[1]: insufficient = st.checkbox("Fictional 8 observed nights", key="kushi_missing_v3")
    with guardrails[2]: thyroid = st.checkbox("Fictional thyroid flag", key="kushi_thyroid_v3")
    changed_flags = dict(flags, hormonal_contraception=contraception, tsh_abnormal=thyroid)
    if insufficient:
        changed_flags["wear_completeness"] = 8 / day
    _forecast_panel(record, day, tier, changed_flags, claims)

    st.markdown("## What this story does and does not show")
    st.markdown("**In plain words:** Every declared generated scenario is listed here. It is not an evaluation dataset or proof of performance.")
    outcomes = []
    for item in cycles:
        item_record = item["record"]
        output = _scenario_output(item_record, day, tier, synthetic_safety_record(item_record, day))
        decision = "Score withheld" if output["abstain"] else ("Flagged" if output["flag"] else "Not flagged")
        outcomes.append({"Scenario cycle": item["logical_cycle"], "Declared seed": item["seed"], "Generated scenario decision": decision})
    st.dataframe(pd.DataFrame(outcomes), hide_index=True, use_container_width=True)
    st.markdown(
        "- This scenario does not diagnose PMOS, confirm ovulation, or infer a hormone level.\n"
        "- The score, timing range, and guardrails are generated-demo behavior, not clinical evidence.\n"
        "- The detailed evidence and failure cases remain available on the Evidence page."
    )
