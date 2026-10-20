"""Home page for the isolated CycleTwin v3 UI; all metrics come from claims."""
from __future__ import annotations

from html import escape

import streamlit as st


GUIDED_STEPS = (
    ("s223-p0000", 2, "Notice the temperature trace, missing nights, and the clearly failed timing range."),
    ("s223-p0026", 2, "Notice the explicit reason that withholds every personal forecast output."),
    ("s223-p0002", 0, "Notice the one-alert policy using the calendar-only Tier 0 display."),
)


def _start_guided_demo() -> None:
    patient, tier, _ = GUIDED_STEPS[0]
    st.session_state.update(
        guided_demo=True, guided_step=0, selected_patient=patient,
        v3_patient_picker=patient, display_tier=tier, view="One patient",
    )


def _card(title: str, value: str, text: str, caption: str, *, danger: bool = False, label: str | None = None, help_text: str | None = None) -> str:
    cls = "ct-card ct-card-danger" if danger else "ct-card"
    hint = f' title="{escape(help_text)}"' if help_text else ""
    label_html = f'<span class="ct-failed-label">⚠ {escape(label)}</span>' if label else ""
    return (
        f'<article class="{cls}"{hint}>{label_html}<h3>{escape(title)}</h3>'
        f'<div class="ct-card-number">{escape(value)}</div><p>{escape(text)}</p>'
        f'<p class="ct-caption ct-muted">{escape(caption)}</p></article>'
    )


def _plain_or_detailed(simple: str, detailed: str, language: str) -> str:
    return detailed if language == "Detailed" else simple


def render_home(*, claims: dict, frozen_summary: list[dict], go_to, language: str) -> None:
    main_day = max(row["Forecast day"] for row in frozen_summary)
    first_day = min(row["Forecast day"] for row in frozen_summary)
    sensor_tiers = [row["Tier"] for row in frozen_summary if "EHR" not in row["Inputs"]]
    main_tier = max(sensor_tiers)
    main_result = next(row for row in frozen_summary if row["Forecast day"] == main_day and row["Tier"] == main_tier)
    early_result = next(row for row in frozen_summary if row["Forecast day"] == first_day and row["Tier"] == main_tier)
    frozen = claims["frozen"]
    seed_count = len(frozen["seeds"])
    conformal = claims["conformal"]
    target = 1 - float(conformal["protocol"]["alpha"])
    conformal_rows = [
        row for key, row in conformal["results"].items()
        if f"day_{main_day}_tier_{main_tier}" in key
    ]
    safety_coverage = sum(row["overall"]["classification_coverage"] for row in conformal_rows) / len(conformal_rows)
    day_band_coverage = sum(row["overall"]["ovulation_day_band_coverage"] for row in conformal_rows) / len(conformal_rows)
    context = claims["context"]["india_prevalence"]

    st.markdown('<span class="ct-badge">◌ Synthetic research prototype · no real patients</span>', unsafe_allow_html=True)
    st.markdown("# CycleTwin")
    st.markdown(
        '<p class="ct-lead">An early-warning research demo for cycles where ovulation may come late or may not happen.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "CycleTwin tests whether cycle history and wearable-style signals can produce an early warning from information available so far. "
        "Everything shown here is computer-generated: there are no real people, no hormone tests, and no diagnosis."
    )
    tour, evidence, _ = st.columns([1, 1, 2])
    tour.button("Start the 60-second tour", type="primary", on_click=_start_guided_demo)
    evidence.button("Explore the evidence", on_click=go_to, args=("Evidence",))

    st.markdown("## What is it?")
    st.markdown(
        "CycleTwin is a research prototype. It uses generated cycle histories and wearable-style observations to demonstrate "
        "a probability for late or missing ovulation. It can also hold back a score when its explicit rules say a simulated record is not suitable."
    )

    st.markdown("## Why it matters")
    st.markdown(
        f"Cycles can vary for many reasons. When ovulation comes late or does not happen in a cycle, it can make a cycle harder to interpret and may be worth discussing with a clinician in a real setting. "
        f"A cited Indian study estimated PMOS prevalence at {context['nih_percent']:.1f}% using NIH criteria and {context['rotterdam_percent']:.1f}% using Rotterdam criteria; those percentages measure how prevalence changes with the diagnostic definition. "
        f"They are background context, not CycleTwin data or a diagnosis. [Read the published study]({context['url']})."
    )

    st.markdown("## How it works")
    how_it_works = (
        ("1", "Generated patients", "We create synthetic cycle histories and wearable-style observations. No real patient information is used."),
        ("2", "A forecast from today’s information", "The model reads only the cycle history and signals available by the selected day."),
        ("3", "Safety checks before a score", "The demo holds back a score when its explicit rules say the simulated record is not suitable."),
    )
    cards = "".join(
        f'<article class="ct-card ct-step"><span class="ct-step-index">{number}</span><h3>{escape(title)}</h3><p>{escape(text)}</p></article>'
        for number, title, text in how_it_works
    )
    st.markdown(f'<div class="ct-grid ct-grid-3">{cards}</div>', unsafe_allow_html=True)

    st.markdown("## What we found")
    detail = language == "Detailed"
    cards = [
        _card(
            "How well it spots higher-risk cycles", f"{main_result['Mean AUROC']:.3f}",
            f"Score from 0.5 (coin flip) to 1.0 (perfect). Tier {main_result['Tier']}, day {main_result['Forecast day']}, generated cycles only.",
            _plain_or_detailed(
                "",
                f"AUROC · Tier {main_result['Tier']} · forecast day {main_result['Forecast day']} · generated cycles only · {main_result['Held-out cycles']:,} held-out cycles across {seed_count} frozen seeds.",
                language,
            ),
            help_text=f"AUROC: higher is better. Brier: {main_result['Mean Brier']:.3f}, lower is better." if not detail else None,
        ),
        _card(
            "Early on, sensors don't help", f"Day {early_result['Forecast day']}",
            f"By day {early_result['Forecast day']} the wearable signals don't improve the forecast yet, so it relies on cycle history alone.",
            _plain_or_detailed(
                "",
                f"Validation-selected feature tier · Tier {early_result['Tier']} · forecast day {early_result['Forecast day']} · generated cycles only.",
                language,
            ),
        ),
        _card(
            "Is the ‘late or not late’ safety range reliable?", f"{safety_coverage:.1%}",
            f"The safety range contained the true answer {safety_coverage:.1%} of the time. Target {target:.0%}. Generated data only.",
            _plain_or_detailed(
                "",
                f"Conformal classification coverage · Tier {main_result['Tier']} · forecast day {main_result['Forecast day']} · generated cycles only.",
                language,
            ),
        ),
        _card(
            "Ovulation-day range: don't use it", f"{day_band_coverage:.1%}",
            f"The true ovulation day fell inside the range only {day_band_coverage:.1%} of the time. It should be about {target:.0%}.",
            _plain_or_detailed(
                "",
                f"Conformal ovulation-day coverage · Tier {main_result['Tier']} · forecast day {main_result['Forecast day']} · generated cycles only.",
                language,
            ),
            danger=True,
            label="Failed",
        ),
    ]
    st.markdown(f'<div class="ct-grid ct-grid-4">{"".join(cards)}</div>', unsafe_allow_html=True)
    if detail:
        st.caption(
            f"Technical detail: Tier {main_result['Tier']} day-{main_result['Forecast day']} mean AUROC is {main_result['Mean AUROC']:.6f}; mean Brier is {main_result['Mean Brier']:.6f}. "
            "AUROC describes ranking; Brier describes probability error. Both are synthetic-only evaluation statistics."
        )

    st.markdown("## Who is it for?")
    audiences = (
        ("Patients", "You can see how a research demo explains a forecast and when it withholds one.", "Do not use it to interpret your own cycle or make health decisions."),
        ("Doctors", "You can inspect the proposed workflow, safety checks, and evidence gaps.", "Do not treat any displayed percentage as a clinical prediction."),
        ("Researchers", "You can inspect a reproducible synthetic benchmark and its failure cases.", "Do not infer real-world performance from generator recovery."),
    )
    audience_cards = "".join(
        f'<article class="ct-card"><h3>{escape(title)}</h3><p><b>What you can do:</b> {escape(can_do)}</p><p class="ct-muted"><b>What not to conclude:</b> {escape(not_conclude)}</p></article>'
        for title, can_do, not_conclude in audiences
    )
    st.markdown(f'<div class="ct-grid ct-grid-3">{audience_cards}</div>', unsafe_allow_html=True)

    st.markdown("## Meet Kushi")
    st.markdown(
        '<article class="ct-card"><h3>A fictional scenario</h3><p>Follow a fictional student’s generated scenario to see the interface in context. '
        'Kushi is not a real person and her story is not performance evidence.</p></article>', unsafe_allow_html=True,
    )
    st.markdown('<div class="ct-action-gap"></div>', unsafe_allow_html=True)
    st.button("Meet Kushi", on_click=go_to, args=("Meet Kushi",))

    st.markdown("## Limits in plain words")
    st.markdown(
        '<aside class="ct-callout"><b>Computer-generated data can prove that this software runs.</b> They cannot prove it works for a person. '
        'CycleTwin is not for diagnosis, contraception, conception planning, or treatment decisions.</aside>', unsafe_allow_html=True,
    )

    st.markdown('<section class="ct-consent"><h2>Before you explore</h2></section>', unsafe_allow_html=True)
    consent = st.checkbox(
        "I understand that CycleTwin uses synthetic data only. It is not a diagnosis, a treatment recommendation, contraception advice, or conception planning support.",
        value=False, key="mock_consent",
    )
    if consent:
        st.success("Mock consent receipt · synthetic demo · no real data")
    else:
        st.info("Select the mock consent receipt to acknowledge the synthetic demonstration.")

    st.markdown(
        '<footer class="ct-footer">Synthetic research prototype. Not for diagnosis, contraception, conception planning, or treatment decisions. '
        '<a href="https://github.com/kushagragupta2005/CycleTwin_VIT" target="_blank" rel="noopener noreferrer">Source code</a> · '
        '<a href="https://github.com/kushagragupta2005/CycleTwin_VIT/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">MIT License</a> · Team CycleTwin</footer>',
        unsafe_allow_html=True,
    )
