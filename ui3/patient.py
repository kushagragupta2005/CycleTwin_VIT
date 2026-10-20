"""Individual generated-record view for the isolated v3 interface."""
from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.alerts import apply_sequential_alert_policy
from src.inference import predict
from src.metabolic import excursion_event
from src.safety import abstention_reasons, synthetic_safety_record
from src.twin import TwinParameters, simulate_metabolic_axis, simulate_reproductive_axis
from src.uncertainty import uncertainty
from ui3.patients import TIER_COPY, demo_cohort


FORECAST_DAY = 14
GUIDED_STEPS = (
    ("s223-p0000", 2, "Notice the temperature trace, missing nights, and the clearly failed timing range."),
    ("s223-p0026", 2, "Notice the explicit reason that withholds every personal forecast output."),
    ("s223-p0002", 0, "Notice the one-alert policy using the calendar-only Tier 0 display."),
)


def _set_guided_step(index: int) -> None:
    patient, tier, _ = GUIDED_STEPS[index]
    st.session_state.update(guided_demo=True, guided_step=index, selected_patient=patient, v3_patient_picker=patient, display_tier=tier)


def _end_guided_demo() -> None:
    st.session_state["guided_demo"] = False
    st.session_state["view"] = "Home"


def _chart_note(text: str) -> None:
    st.markdown(f'<p class="ct-chart-note"><b>Auto-generated from the data shown.</b> {text}</p>', unsafe_allow_html=True)


def _temperature_chart(record: dict, interval: tuple[int, int], coverage_target: float) -> None:
    temperature = pd.DataFrame({"day": np.arange(1, 29), "offset": record["temperature"][:28]})
    missing = temperature[temperature["offset"].isna()].assign(marker=-0.18)
    band = alt.Chart(pd.DataFrame({"start": [interval[0]], "end": [interval[1]]})).mark_rect(
        color="#0c6b68", opacity=0.12
    ).encode(x="start:Q", x2="end:Q", y=alt.value(0), y2=alt.value(270))
    line = alt.Chart(temperature.assign(segment=temperature["offset"].isna().cumsum()).dropna()).mark_line(
        color="#0c6b68", strokeWidth=2.5
    ).encode(
        x=alt.X("day:Q", title="Cycle day"),
        y=alt.Y("offset:Q", title="Temperature offset (°C)", scale=alt.Scale(domain=[-0.25, 0.35])),
        detail="segment:N",
    )
    points = alt.Chart(temperature.dropna()).mark_circle(color="#0c6b68", size=25).encode(
        x="day:Q", y=alt.Y("offset:Q", scale=alt.Scale(domain=[-0.25, 0.35]))
    )
    gaps = alt.Chart(missing).mark_point(shape="cross", color="#526267", size=90).encode(
        x="day:Q", y=alt.Y("marker:Q", scale=alt.Scale(domain=[-0.25, 0.35]))
    )
    start = alt.Chart(pd.DataFrame({"day": [1]})).mark_rule(color="#8a4f00", strokeDash=[4, 3]).encode(x="day:Q")
    st.altair_chart((band + line + points + gaps + start).properties(height=285), use_container_width=True)
    early = temperature.loc[temperature["day"] <= 5, "offset"].dropna()
    late = temperature.loc[temperature["day"] >= 21, "offset"].dropna()
    if not early.empty and not late.empty:
        _chart_note(
            f"Mean temperature offset changed by {late.mean() - early.mean():+.2f}°C from days 1–5 to days 21–28; "
            f"{len(missing)} of {len(temperature)} nights are missing."
        )
    else:
        _chart_note(f"{temperature['offset'].notna().sum()} of {len(temperature)} nightly values are present; {len(missing)} are missing.")
    st.markdown(
        '<div class="ct-inline-legend"><span>▨ Teal band · illustrative estimated day range</span><span>┆ Amber · assumed cycle start</span><span>× Gray · missing night</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Missing nightly temperatures are not filled in. The interval is an illustrative range around a heuristic day estimate; "
        f"its frozen coverage failed the {coverage_target:.0%} target."
    )


def _twin_chart(record: dict, index: int) -> None:
    twin = simulate_reproductive_axis(record["ir"], record["androgen"], seed=4000 + index)
    values = pd.DataFrame({"day": np.arange(1, 36), "follicle": twin["follicle"][:35]})
    curve = alt.Chart(values).mark_line(color="#0c6b68", strokeWidth=2.5).encode(
        x=alt.X("day:Q", title="Cycle day", scale=alt.Scale(domain=[0, 35], nice=False)),
        y=alt.Y("follicle:Q", title="Follicle state (simulated units)"),
        tooltip=[alt.Tooltip("day:Q", title="Cycle day"), alt.Tooltip("follicle:Q", format=".3f")],
    )
    threshold = alt.Chart(pd.DataFrame({"threshold": [TwinParameters().lh_threshold]})).mark_rule(
        color="#8a4f00", strokeDash=[5, 4]
    ).encode(y="threshold:Q")
    st.altair_chart((curve + threshold).properties(title="Twin follicle-growth trajectory", height=235), use_container_width=True)
    high_at = int(values.iloc[int(np.argmax(values["follicle"].to_numpy()))]["day"])
    _chart_note(f"Simulated follicle state ranges from {values['follicle'].min():.2f} to {values['follicle'].max():.2f} units; its highest plotted value is on day {high_at}.")
    event = twin["ovulation_day"] if twin["ovulation_day"] > 0 else "no surge in the simulation window"
    st.caption(f"Simulator event: {event}. This separate twin illustration is not an input to the fitted score.")


def _cgm_panel(record: dict, index: int, twin_day: int) -> None:
    if index % 4:
        st.markdown('<p class="ct-inline-note"><b>CGM illustration:</b> Not sampled for this generated record.</p>', unsafe_allow_html=True)
        return
    simulated = simulate_metabolic_axis(record["ir"], twin_day, seed=3000 + index)
    glucose = simulated["glucose_mg_dl"]
    meals = simulated["meal_indices"]
    excursions = [excursion_event(glucose, meal) for meal in meals]
    downsampled = glucose[::8]
    shown = pd.DataFrame({"minutes": np.arange(len(downsampled)) * simulated["step_minutes"] * 8, "glucose": downsampled})
    trace = alt.Chart(shown).mark_line(color="#0c6b68").encode(
        x=alt.X("minutes:Q", title="Elapsed time (minutes)"), y=alt.Y("glucose:Q", title="Glucose (mg/dL)")
    )
    rule = alt.Chart(pd.DataFrame({"reference": [140]})).mark_rule(color="#8a4f00", strokeDash=[5, 4]).encode(y="reference:Q")
    st.altair_chart((trace + rule).properties(title="Synthetic CGM illustration", height=250), use_container_width=True)
    _chart_note(f"Simulated glucose exceeded 140 mg/dL within 120 minutes after {sum(excursions)} of {len(excursions)} meal windows.")
    st.caption("Synthetic 15-minute values only; this is not a clinical glucose forecast or evaluated endpoint.")


def _add_alert(record: dict, patient: str, tier: int) -> None:
    predictions = []
    for row in demo_cohort():
        for day in (10, 14, 18):
            reasons = abstention_reasons(synthetic_safety_record(row, day))
            output = predict(row, day, tier)
            predictions.append({"patient": row["patient"], "cycle": row["cycle"], "day": day, "risk": output["prob"], "threshold": output["threshold"], "abstain": bool(reasons)})
    selected = next((item for item in apply_sequential_alert_policy(predictions) if item["patient"] == patient and item["alert"]), None)
    log = st.session_state.setdefault("alert_log", [])
    if selected is None:
        st.warning("No eligible synthetic alert was selected for this patient-cycle under the one-alert policy.")
    elif any(item["patient"] == patient and item["cycle"] == selected["cycle"] for item in log):
        st.info("This synthetic patient-cycle is already in the one-alert log.")
    else:
        log.append({key: selected[key] for key in ("patient", "cycle", "day", "risk")})
        st.success("Added the earliest eligible synthetic alert for this cycle.")


def render_patient(*, language: str, claims: dict) -> None:
    detailed = language == "Detailed"
    records = demo_cohort()
    ids = [record["patient"] for record in records]
    current = st.session_state.get("selected_patient", ids[0])
    if current not in ids:
        current = ids[0]
    selected = st.selectbox("Generated record", ids, index=ids.index(current), key="v3_patient_picker")
    st.session_state["selected_patient"] = selected
    record = next(row for row in records if row["patient"] == selected)
    tier = st.session_state.get("display_tier", 2)
    if tier not in TIER_COPY:
        tier = 2
    flags = synthetic_safety_record(record, FORECAST_DAY)
    reasons = abstention_reasons(flags)
    output = predict(record, FORECAST_DAY, tier)
    withheld = bool(reasons)
    index = int(selected.rsplit("p", 1)[-1])
    coverage_target = 1 - float(claims["conformal"]["protocol"]["alpha"])

    if st.session_state.get("guided_demo", False):
        step = int(st.session_state.get("guided_step", 0))
        _, _, notice = GUIDED_STEPS[step]
        st.markdown('<section class="ct-tour"><b>Guided tour</b><br>' + notice + "</section>", unsafe_allow_html=True)
        back, progress, next_step = st.columns([1, 2, 1])
        with back:
            st.button("Back", disabled=step == 0, on_click=_set_guided_step, args=(step - 1,), key="v3_tour_back")
        with progress:
            st.progress((step + 1) / len(GUIDED_STEPS), text=f"Step {step + 1} of {len(GUIDED_STEPS)} · {selected}")
        with next_step:
            if step == len(GUIDED_STEPS) - 1:
                st.button("Finish", on_click=_end_guided_demo, key="v3_tour_finish")
            else:
                st.button("Next", on_click=_set_guided_step, args=(step + 1,), key="v3_tour_next")

    st.markdown('<span class="ct-badge">◌ Synthetic data only · generated research record</span>', unsafe_allow_html=True)
    st.markdown(f"# {selected}")
    st.markdown("Inspect one generated cycle. The score forecasts the simulator’s late-or-absent-ovulation label; it does not diagnose PMOS or describe a real person.")
    st.caption(f"Tier {tier} · forecast day {output['day']} · generated archetype: {record['phenotype']}")

    with st.expander(f"Model card · Tier {tier} · day {output['day']}"):
        metrics = output["metrics"]
        st.markdown("**In plain words:** These held-out synthetic metrics describe the model version used for this display, not confidence for this record.")
        st.dataframe(pd.DataFrame([{
            "AUROC": metrics["auroc"], "Brier": metrics["brier"], "Held-out cycles": metrics["n_cycles"],
            "AUROC 95% CI": f"{metrics['auroc_cluster_bootstrap_95ci'][0]:.3f}–{metrics['auroc_cluster_bootstrap_95ci'][1]:.3f}",
        }]), hide_index=True, use_container_width=True)
        st.caption("Synthetic held-out data only. The confidence interval groups cycles by generated patient; it is not an individual confidence guarantee.")

    if withheld:
        st.markdown(
            '<section class="ct-abstain"><b>⏸ Score withheld · clinician review state</b><br>Rule fired: ' + "; ".join(reasons) + "</section>",
            unsafe_allow_html=True,
        )
        st.markdown("**In plain words:** The display withholds the score, interval, feature evidence, sandbox, and alerts when this explicit safety rule fires.")
        _temperature_chart(record, (FORECAST_DAY, FORECAST_DAY), coverage_target)
        return

    interval_info = uncertainty(record, FORECAST_DAY, tier, output)
    estimate, interval = interval_info["estimate"], interval_info["interval"]
    score, details = st.columns([1, 1.55])
    with score:
        label = "! Flagged for review" if output["flag"] else "○ Not flagged"
        cls = "flagged" if output["flag"] else "neutral"
        st.markdown(f'<span class="ct-status ct-status-{cls}">{label}</span>', unsafe_allow_html=True)
        st.metric("Fitted synthetic forecast score", f"{output['prob']:.0%}", help="Probability for the generator’s late-or-absent-ovulation label. It is not a diagnosis probability.")
        st.caption(f"Validation-selected threshold: {output['threshold']:.3f}")
    with details:
        st.markdown("### Cycle summary")
        st.markdown(f"**Illustrative day estimate:** day {estimate}; range day {interval[0]}–{interval[1]}.")
        st.markdown("**In plain words:** The number is produced from generated cycle history and wearable-style signals available by the forecast day.")
        st.caption(
            "The day range is a synthetic calibration illustration. Its frozen coverage did not meet the "
            f"{coverage_target:.0%} target, so it must not be relied on as an uncertainty guarantee."
        )

    st.markdown("## Temperature trace")
    st.markdown("**In plain words:** Generated nightly temperature offsets are shown as observed, including missing nights.")
    _temperature_chart(record, interval, coverage_target)

    st.markdown("## Twin trajectory")
    st.markdown("**In plain words:** This is a separate day-by-day simulator display. The fitted score does not use it.")
    _twin_chart(record, index)

    st.markdown("## CGM illustration")
    st.markdown("**In plain words:** Where shown, this independent simulated glucose stream is displayed beside the cycle forecast.")
    twin_day = simulate_reproductive_axis(record["ir"], record["androgen"], seed=4000 + index)["ovulation_day"]
    _cgm_panel(record, index, twin_day)

    with st.expander("Exact fitted feature evidence", expanded=detailed):
        st.caption("Coefficient × standardized input from the persisted fitted model. These values show association inside the simulator, not causation.")
        st.dataframe(pd.DataFrame(output["contributions"]), hide_index=True, use_container_width=True)

    st.markdown("## Assumption sandbox")
    st.markdown("**In plain words:** Edit an invented prior-cycle average and rerun the same fitted synthetic classifier. This is not a treatment or intervention forecast.")
    history = np.asarray(record["prior_cycle_lengths"], dtype=float)
    edited = st.number_input("Invented prior-cycle mean (days)", value=float(history.mean()), key="v3_sandbox_history")
    if st.button("Run synthetic assumption sandbox", key="v3_sandbox_button"):
        altered = dict(record, prior_cycle_lengths=[edited] * len(history))
        altered_output = predict(altered, FORECAST_DAY, tier)
        st.info(f"Edited synthetic-input score: {altered_output['prob']:.1%}; validation threshold {altered_output['threshold']:.3f}.")
        st.caption("No lifestyle multiplier or causal effect is calculated.")

    st.markdown("## Synthetic alert log")
    st.markdown("**In plain words:** An eligible patient-cycle can be retained once, at its earliest threshold crossing across the available forecast days.")
    if st.button("Add selected synthetic alert to log", key="v3_add_alert", on_click=_add_alert, args=(record, selected, tier)):
        pass
    log = st.session_state.get("alert_log", [])
    if log:
        st.dataframe(pd.DataFrame(log), hide_index=True, use_container_width=True)
    else:
        st.caption("No synthetic alerts have been added in this browser session.")
    st.caption("At most one alert per synthetic patient-cycle. Scores withheld by safety rules cannot enter the log.")
