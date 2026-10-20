"""Judge-facing synthetic narrative; deterministic calculations, no language model."""
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from src.claims import load_claims
from src.inference import safe_predict
from src.personas import make_kushi
from src.safety import synthetic_safety_record
from src.uncertainty import uncertainty
from src.reporting_ui import render_reporting, render_alert_policy, render_robustness, render_bayesian_twin, render_lab_proxy, render_operations, render_conformal

CHAPTERS = ("Meet Kushi", "Her two data streams", "Her twin wakes up", "What her doctor sees",
            "Guardrails live", "Where it fails", "The evidence")


def _move(delta):
    st.session_state["kushi_chapter"] = max(0, min(len(CHAPTERS)-1, st.session_state.get("kushi_chapter", 0)+delta))


def _output(record, day, tier, flags=None):
    return safe_predict(record, day, tier, safety=flags if flags is not None else synthetic_safety_record(record, day))


def _show_forecast(record, day, tier, flags=None):
    output = _output(record, day, tier, flags)
    st.session_state["kushi_visible_prediction"] = output
    if output["abstain"]:
        st.warning("Abstain · " + "; ".join(output["reasons"]))
        st.caption("Personal probability, uncertainty, evidence, sandbox and alerts are withheld.")
        return output
    band = uncertainty(record, day, tier, output)
    cols = st.columns(3)
    cols[0].metric("Fitted synthetic probability", f"{output['prob']:.1%}", help="Generated late/absent-ovulation label; not diagnosis or clinical probability.")
    cols[1].metric("Validation threshold", f"{output['threshold']:.6f}", help="Chosen by validation F1, never by the displayed persona or test outcomes.")
    cols[2].metric("Synthetic decision", "Flagged" if output["flag"] else "Not flagged", help="Not flagged does not mean clinical reassurance.")
    if output["fallback_used"]:
        st.info("Calendar fallback selected · richer features did not pass the validation rule.")
    st.write(f"Heuristic ovulation-day estimate: {band['estimate']}; illustrative day band {band['interval'][0]}–{band['interval'][1]}.")
    st.caption("Day band conditional on an ovulatory cycle; no date exists for absent ovulation. Marginal synthetic illustration, not a personal guarantee; frozen empirical coverage is pending.")
    st.write(f"Synthetic class set: {band['class_set']} · both labels means the set does not choose one outcome.")
    metric = output["metrics"]
    st.caption(f"This persisted model · synthetic development AUROC {metric['auroc']:.6f}; Brier {metric['brier']:.6f}; n={metric['n_cycles']}. Not clinical validation.")
    st.dataframe(pd.DataFrame(output["contributions"]), hide_index=True, use_container_width=True)
    st.caption("Exact coefficient × standardized-value evidence. Calibrated contributions plus intercept reproduce the final logit. Associations are not causes.")
    return output


def render_kushi():
    claims = load_claims()
    persona = make_kushi()
    profile = claims["kushi"]["profile"]
    st.warning(profile["scope"])
    chapter = st.session_state.setdefault("kushi_chapter", 0)
    st.subheader(CHAPTERS[chapter])
    st.caption(f"Chapter {chapter+1} of {len(CHAPTERS)} · synthetic story")
    back, forward = st.columns(2)
    back.button("Previous chapter", on_click=_move, args=(-1,), disabled=chapter == 0)
    forward.button("Next chapter", on_click=_move, args=(1,), disabled=chapter == len(CHAPTERS)-1)
    st.progress((chapter+1)/len(CHAPTERS))
    controls = st.columns(3)
    with controls[0]:
        cycle = st.selectbox("Synthetic scenario cycle", [s["logical_cycle"] for s in persona["cycles"]], key="kushi_cycle")
    with controls[1]:
        tiers = sorted({int(k.rsplit('_', 1)[1]) for k in next(iter(claims['development']['seeds'].values()))['metrics']})
        tier = st.selectbox("Kushi input tier", tiers, index=len(tiers)-1, key="kushi_tier",
                            format_func=lambda t:f"Tier {t}"+(" · oracle-adjacent EHR-lite" if t == max(tiers) else ""))
    with controls[2]:
        days = sorted({int(k.split('_')[1]) for k in next(iter(claims['development']['seeds'].values()))['metrics']})
        day = st.select_slider("Available forecast snapshot", options=days, value=days[len(days)//2], key="kushi_day")
    scenario = next(s for s in persona['cycles'] if s['logical_cycle'] == cycle)
    record = scenario['record']
    st.caption(f"Generated scenario seed {scenario['seed']} · cycle {cycle}. {persona['scenario_disclosure']}")

    if chapter == 0:
        st.markdown(f"**{profile['name']} · {profile['age']} · year {profile['study_year']} {profile['course']}**")
        st.write(profile['story'])
        st.write(f"Fictional reported usual cycle range: {profile['usual_reported_cycle_range'][0]}–{profile['usual_reported_cycle_range'][1]} days. Generated past lengths are shown unchanged.")
        st.dataframe(pd.DataFrame({'Past cycle':range(1,len(persona['six_past_lengths'])+1),'Generated length (days)':persona['six_past_lengths']}), hide_index=True)
        context = claims['context']['india_prevalence']
        st.markdown(f"**India context:** the cited study reports {context['nih_percent']}% by NIH criteria and {context['rotterdam_percent']}% by Rotterdam criteria. Estimates depend on definition; these are not CycleTwin data or performance. [Published study]({context['url']}).")
        with st.expander("How this example was selected"):
            st.write(persona['selection_rule'])
            st.caption("Profile age, BMI and family history are explicit fictional overrides. Sleep debt is narrative context, not an imposed generator effect.")
    elif chapter == 1:
        st.markdown("**Static stream · synthetic EHR-lite**")
        st.dataframe(pd.DataFrame([{'Age':record['age'],'BMI':record['bmi'],'Family history':record['family_history'],
                                    'Simulator IR latent':record['ir'],'Simulator androgen':record['androgen']}]), hide_index=True)
        st.caption("Oracle-adjacent simulator values, not measured hormone levels or real EHR. Only the retained model features affect the score.")
        st.markdown("**Dynamic stream · generated nightly observations**")
        data = pd.DataFrame({'Cycle day':np.arange(1,day+1),'Temperature offset (°C)':record['temperature'][:day],
                             'RHR offset (synthetic units)':record['rhr'][:day],
                             'HRV offset (synthetic units)':record['hrv'][:day],
                             'Sleep (hours)':record['sleep'][:day],'Steps':record['steps'][:day]}).set_index('Cycle day')
        for name in data:
            st.line_chart(data[[name]])
        st.caption(f"Missing temperatures: {int(data.iloc[:,0].isna().sum())}/{len(data)}. Missing nights remain missing; no interpolation or hormone inference.")
    elif chapter == 2:
        st.caption("Current evaluated prediction engine: fitted logistic classifier. The illustrative physiological simulator remains separate; a Bayesian nightly twin has not yet been implemented.")
        snapshots = []
        for d in days:
            out = _output(record,d,tier)
            snapshots.append({'Synthetic day':d,'Probability':out['prob'],'Threshold':out.get('threshold'),
                              'Status':'Withheld' if out['abstain'] else ('Flagged' if out['flag'] else 'Not flagged'),
                              'Retained tier':out.get('selected_tier')})
        st.dataframe(pd.DataFrame(snapshots), hide_index=True)
        _show_forecast(record,day,tier)
    elif chapter == 3:
        st.markdown("**Clinician research view · decision support, not diagnosis**")
        flags = synthetic_safety_record(record,day)
        st.caption(f"Data quality: {int(np.isfinite(record['temperature'][:day]).sum())}/{day} temperatures observed. Safety inputs explicitly supplied from synthetic metadata.")
        _show_forecast(record,day,tier,flags)
        st.markdown("**Discussion prompts for a qualified clinician**")
        st.write("Consider whether and when confirmatory ovulation assessment is appropriate, including appropriately timed progesterone testing or discussion of urinary LH limitations. This screen neither orders tests nor interprets them for a person.")
        st.markdown(f"[Clinical context source]({claims['context']['ovulation_confirmation']['url']})")
    elif chapter == 4:
        contra = st.checkbox("Starts hormonal contraception",key="kushi_contra")
        missing = st.checkbox("Watch worn 8/14 nights",key="kushi_missing")
        thyroid = st.checkbox("Thyroid flag",key="kushi_thyroid")
        flags = synthetic_safety_record(record,14)
        flags.update(hormonal_contraception=contra,tsh_abnormal=thyroid)
        if missing: flags['wear_completeness']=8/14
        st.caption("Guardrails use the declared demonstration snapshot. Flags are synthetic user-controlled scenarios, not diagnoses.")
        _show_forecast(record,14,tier,flags)
    elif chapter == 5:
        outcomes=[]
        for sample in persona['cycles']:
            row=sample['record']; out=_output(row,day,tier)
            status='Withheld' if out['abstain'] else ('Miss' if row['event'] and not out['flag'] else 'False alarm' if not row['event'] and out['flag'] else 'Matches generated label')
            outcomes.append({'Cycle':sample['logical_cycle'],'Declared seed':sample['seed'],
                             'Generated ovulation day':row['ovulation_day'],'Generated event':row['event'],
                             'Fitted probability':out['prob'],'Decision':status})
        st.dataframe(pd.DataFrame(outcomes),hide_index=True)
        st.caption("Every declared scenario is shown, including misses, false alarms and withholding. These examples are not an evaluation sample or performance estimate.")
        render_robustness(claims)
        st.write("Synthetic assumptions can fail in people. No clinical validation, hormone inference, causal treatment model or PMOS diagnosis is available.")
    else:
        if claims['frozen'] is None:
            st.info("Frozen-seed evaluation is pending; current results are development evidence.")
        else:
            st.caption("Frozen synthetic results are available; these still do not establish clinical validity.")
            st.dataframe(pd.DataFrame(claims['frozen_summary']),hide_index=True,use_container_width=True)
        with st.expander('Development results: older seeds'):
            st.dataframe(pd.DataFrame(claims['summary']),hide_index=True,use_container_width=True)
        render_reporting(claims,tier)
        render_alert_policy(claims)
        render_bayesian_twin(claims)
        render_lab_proxy(claims)
        render_operations(claims)
        render_conformal(claims)
        st.markdown('[Implementation audit](https://github.com/kushagragupta2005/CycleTwin_VIT/blob/main/docs/audit_2026-10-20/CycleTwin_full_audit.md) · [Generated claims](https://github.com/kushagragupta2005/CycleTwin_VIT/blob/main/docs/claims.json)')
        st.write("Sim-to-real statement: recovering labels from this generator is not evidence of reliable forecasts in women. Independent measurements and prospective validation remain necessary.")
