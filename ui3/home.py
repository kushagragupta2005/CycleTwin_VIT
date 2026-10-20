"""Home page for the isolated CycleTwin v3 UI; all metrics come from claims."""
from __future__ import annotations

from html import escape

import streamlit as st


def _card(title: str, value: str, text: str, caption: str, *, danger: bool = False, help_text: str | None = None) -> str:
    cls = "ct-card ct-card-danger" if danger else "ct-card"
    hint = f' title="{escape(help_text)}"' if help_text else ""
    return (
        f'<article class="{cls}"{hint}><h3>{escape(title)}</h3>'
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
    conformal_rows = [row for key, row in conformal["results"].items() if "day_18_tier_2" in key]
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
    tour, evidence = st.columns(2)
    tour.button("Start the 60-second tour", type="primary", on_click=go_to, args=("One patient",))
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
            f"Day-{main_result['Forecast day']} forecast quality", f"{main_result['Mean AUROC']:.3f}",
            f"How well Tier {main_result['Tier']} separates generated late-or-missing cycles on day {main_result['Forecast day']}.",
            f"Tier {main_result['Tier']} · forecast day {main_result['Forecast day']} · generated data only · {main_result['Held-out cycles']:,} held-out cycles across {seed_count} frozen seeds.",
            help_text=f"AUROC: higher is better. Brier: {main_result['Mean Brier']:.3f}, lower is better." if not detail else None,
        ),
        _card(
            "Early snapshot", f"Day {early_result['Forecast day']}",
            "Added simulated sensors did not improve the result yet.",
            f"Tier {early_result['Tier']} · forecast day {early_result['Forecast day']} · generated data only.",
            help_text=f"AUROC: {early_result['Mean AUROC']:.3f}; Brier: {early_result['Mean Brier']:.3f}." if not detail else None,
        ),
        _card(
            "Classification safety range", f"{safety_coverage:.1%}",
            "Coverage of the classification safety range in the generated evaluation.",
            f"Tier {main_result['Tier']} · forecast day {main_result['Forecast day']} · generated data only · target: {target:.0%}.",
        ),
        _card(
            "Do not rely on this", f"{day_band_coverage:.1%} / {target:.0%}",
            "The ovulation-day band failed its coverage check.",
            f"Tier {main_result['Tier']} · forecast day {main_result['Forecast day']} · generated data only · observed coverage / target.",
            danger=True,
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
