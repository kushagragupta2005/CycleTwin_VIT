"""Evidence page for the isolated v3 interface; values come from claims.json."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def _results_table(frozen_summary: list[dict]) -> pd.DataFrame:
    rows = []
    for row in frozen_summary:
        rows.append({
            "Forecast day": row["Forecast day"], "Tier": row["Tier"], "Information used": row["Inputs"],
            "AUROC": row["Mean AUROC"], "Brier": row["Mean Brier"], "Held-out cycles": row["Held-out cycles"],
            "Seeds retaining feature set": row["Seeds retaining candidate"],
        })
    return pd.DataFrame(rows)


def _alert_table(summary: dict) -> pd.DataFrame:
    return pd.DataFrame([{
        "Tier": int(tier), "Synthetic cycles": item["n_cycles"], "Alerts": item["alerts"],
        "Alert precision": item["alert_precision"], "Missed-event rate": item["missed_event_rate"],
        "False alerts / synthetic patient-year": item["false_alerts_per_synthetic_patient_year"],
    } for tier, item in summary.items()])


def render_evidence(*, claims: dict, language: str) -> None:
    detailed = language == "Detailed"
    summary = claims["frozen_summary"]
    main_day = max(row["Forecast day"] for row in summary)
    sensor_tiers = [row["Tier"] for row in summary if "EHR" not in row["Inputs"]]
    main_tier = max(sensor_tiers)
    main = next(row for row in summary if row["Forecast day"] == main_day and row["Tier"] == main_tier)
    target = 1 - float(claims["conformal"]["protocol"]["alpha"])
    conformal = claims["conformal_summary"]

    st.markdown('<span class="ct-badge">◌ Synthetic data only · held-out simulator evaluation</span>', unsafe_allow_html=True)
    st.markdown("# Evidence")
    st.markdown("This page shows what was measured in generated held-out cycles, what was not measured, and the limits that keep it from being clinical evidence.")

    st.markdown("## What was evaluated")
    st.markdown(
        "**In plain words:** The generator creates cycles, a logistic-regression model is fit on one generated split, and results are measured on separate generated cycles. "
        "These are reproducibility checks inside one simulator, not evidence of performance for people."
    )
    cards = (
        ("Fitted model", "Logistic regression", "Fit on generated training data; probability calibration and the flag threshold are chosen on generated validation data."),
        ("Primary display", f"Tier {main_tier}, day {main_day}", "Cycle history, wearable-style signals, and nightly temperature. The extra EHR-lite tier is a simulator-internal, oracle-adjacent check."),
        ("Evaluation", f"{main['Held-out cycles']:,} generated cycles", "Metrics are averaged across the frozen random seeds. No real participant, hormone measurement, or external cohort is included."),
    )
    card_html = "".join(
        f'<article class="ct-card"><h3>{title}</h3><div class="ct-card-number ct-card-number-small">{value}</div><p>{body}</p></article>'
        for title, value, body in cards
    )
    st.markdown(f'<div class="ct-grid ct-grid-3">{card_html}</div>', unsafe_allow_html=True)

    st.markdown("## Frozen results by information tier")
    st.markdown("**In plain words:** Higher AUROC means the model ranks generated late-or-missing cycles ahead of other generated cycles more often. Lower Brier means smaller probability error inside this simulator.")
    st.dataframe(_results_table(summary), hide_index=True, use_container_width=True)
    st.caption("Every row is generated data only. A retained feature count of zero means validation kept the simpler calendar feature set for that requested tier.")

    st.markdown("## Uncertainty and safety checks")
    st.markdown("**In plain words:** The classification safety range reached its generated-data target on average. The separate ovulation-day range did not and remains visibly failed.")
    uncertainty = pd.DataFrame([{
        "Classification coverage": conformal["classification_coverage_mean"],
        "Classification target": target,
        "Mean classification-set size": conformal["mean_classification_set_size"],
        "Ovulation-day coverage (failed)": conformal["day_band_coverage_mean"],
        "Mean day-range width": conformal["day_band_mean_width"],
    }])
    st.dataframe(uncertainty, hide_index=True, use_container_width=True)
    st.markdown('<aside class="ct-callout"><b>⚠ Failed timing range.</b> The ovulation-day range did not achieve the documented coverage target in frozen generated evaluation. It is an illustration, not a reliable timing interval.</aside>', unsafe_allow_html=True)

    st.markdown("## Alert-policy check")
    st.markdown("**In plain words:** The demo permits one eligible alert per generated patient-cycle and retains the earliest threshold crossing. These counts are not clinical alert rates.")
    st.dataframe(_alert_table(claims["alert_policy_summary"]), hide_index=True, use_container_width=True)

    with st.expander("Diagnostics and local runtime details", expanded=detailed):
        st.markdown("**In plain words:** These are extra generated-data diagnostics. They do not alter the saved model or prove reliability on external data.")
        operations = claims.get("operations")
        if operations:
            warm = operations["warm_latency_ms"]
            st.dataframe(pd.DataFrame([{
                "Cold subprocess (ms)": operations["cold_subprocess_ms"], "Warm mean (ms)": warm["mean"],
                "Warm p95 (ms)": warm["p95"], "Warm repeats": operations["warm_repeats"],
                "Process peak RSS (KiB)": operations["process_peak_rss_kib"],
            }]), hide_index=True, use_container_width=True)
            st.caption(operations["rss_note"])
        for filename, caption in (
            ("reliability.svg", "Frozen synthetic reliability by snapshot; counts pool separate seed models."),
            ("decision_curve.svg", "Frozen synthetic day-18 decision curves; threshold odds are assumptions."),
        ):
            figure = Path("docs/figures") / filename
            if figure.exists():
                st.image(str(figure), caption=caption)

    st.markdown("## Limits that matter")
    st.markdown(
        "- The simulator creates the relationships the model learns, so strong synthetic results can reflect generator recovery.\n"
        "- No clinical cohort, diagnosis labels, measured hormones, device validation, or external validation is present.\n"
        "- EHR-lite includes simulator internal variables that also shape the generated label; it is an oracle-adjacent check, not EHR fusion.\n"
        "- The twin and CGM illustrations are separate demonstrations, not inputs to the primary fitted score."
    )
