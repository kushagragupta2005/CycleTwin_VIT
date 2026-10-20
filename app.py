"""Local synthetic-data dashboard. No clinical workflow or personal export is used."""
from pathlib import Path
from html import escape
import subprocess
import sys
import json
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.generator import generate
from src.claims import load_claims
from src.kushi_ui import render_kushi
from src.reporting_ui import render_reporting, render_alert_policy, render_robustness, render_bayesian_twin
from src.model import estimate_ovulation_day
from src.inference import predict, safe_predict
from src.features import attach_prior_cycle_lengths
from src.uncertainty import uncertainty
from src.safety import abstention_reasons, synthetic_safety_record
from src.conformal import calibrate_binary, calibrate_ovulation_interval, classification_set, ovulation_interval
from src.alerts import apply_alert_budget, apply_sequential_alert_policy
from src.metabolic import excursion_event
from src.twin import simulate_reproductive_axis, simulate_metabolic_axis, coupling_sweep, TwinParameters
from src.adapters.apple_health import parse_export, parse_upload_bytes

DISCLAIMER="Not for diagnosis, contraception or conception planning. Synthetic demonstration only."
st.set_page_config(page_title="CycleTwin synthetic demo", layout="wide", initial_sidebar_state="auto")
st.markdown("""
<style>
:root { --ink:#17242b; --muted:#65757b; --teal:#0e766e; --teal-soft:#e8f4f1; --amber:#a66c13; --amber-soft:#fff7e6; --line:#e3e9e7; }
.stApp { background:#fafaf8; color:#17242b; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.55; }
.block-container { max-width:1440px; padding:2.5rem 3rem 6rem; }
h1, h2, h3 { color:#17242b; letter-spacing:-0.025em; }
h1 { font-size:2.45rem; line-height:1.15; font-weight:500; margin:0 0 1.5rem; }
h2 { font-size:1.65rem; line-height:1.3; font-weight:500; margin:2.5rem 0 1rem; }
h3 { font-size:1.2rem; line-height:1.4; font-weight:500; }
[data-testid="stSidebar"] > div:nth-child(1) { padding:1.5rem 1.1rem; }
[data-testid="stHorizontalBlock"] { gap:2rem; }
[data-testid="stMetric"], [data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border:1px solid #e8ecea; border-radius:16px; padding:1.25rem; box-shadow:0 4px 18px rgba(23,36,43,.035); }
[data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricValue"], [data-testid="stMetric"] [data-testid="stMetricDelta"] { color:var(--ink) !important; }
.cycletwin-note { color:var(--muted); font-size:0.86rem; }
.cycletwin-neutral { color:var(--muted); font-size:0.86rem; }
input[type="range"] { accent-color: var(--teal); }
.abstain-card { border:1px solid #eadbb9; background:#fffaf0; border-radius:16px; padding:1.1rem 1.25rem; color:var(--ink); box-shadow:0 4px 18px rgba(23,36,43,.035); }
.status-pill { display:inline-block; border-radius:999px; padding:3px 9px; font-size:.82rem; white-space:nowrap; }
.status-neutral { background:#edf1f2; color:#52616a; }
.status-review { background:#fff0cf; color:#77500a; }
.status-flagged { background:#e5f3f0; color:#175d56; }
.demo-footer { position:fixed; z-index:999; left:0; right:0; bottom:0; padding:8px 1rem; background:#18313d; color:#fff; text-align:center; font-size:.82rem; }
.demo-footer a { color:#d4ebe5; margin-right:1rem; }
.block-container { padding-bottom:6rem; }
button, [data-testid^="stBaseButton-"] { min-height:2.65rem; border-radius:10px; border-color:#dce3e1; box-shadow:none; transition:background-color .15s ease,border-color .15s ease,color .15s ease; }
button:hover, [data-testid^="stBaseButton-"]:hover { border-color:var(--teal); color:var(--teal); }
button:focus-visible, input:focus-visible, [role="combobox"]:focus-visible { outline:2px solid var(--teal); outline-offset:2px; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div { min-height:2.65rem; border-radius:10px; }
.chart-summary { margin:.35rem 0 1.5rem; padding:.25rem 0 .25rem .9rem; border-left:2px solid #d9e6e2; color:#36464d; font-size:.92rem; line-height:1.5; }
.chart-summary-label { display:block; margin-top:.2rem; color:var(--muted); font-size:.75rem; }
.synthetic-badge { display:inline-block; background:var(--teal-soft); color:var(--teal); border-radius:999px; padding:.3rem .8rem; font-size:.78rem; font-weight:600; margin:.7rem 0; }
.hero-copy { max-width:58rem; font-size:1.3rem; line-height:1.5; color:var(--ink); margin-bottom:.5rem; }
.plain-words { color:var(--muted); font-size:.92rem; line-height:1.55; margin:.3rem 0 1rem; }
.workflow-grid { display:grid; grid-template-columns:1fr auto 1fr auto 1fr; align-items:center; gap:1rem; margin:1rem 0; }
.workflow-card,.feature-card { background:white; border:1px solid var(--line); border-radius:16px; padding:1.2rem; box-shadow:0 5px 20px rgba(23,36,43,.025); }
.workflow-card strong,.feature-card strong { display:block; margin-bottom:.4rem; font-size:1rem; font-weight:500; }
.workflow-card p,.feature-card p { margin:0; color:var(--muted); font-size:.9rem; line-height:1.5; }
.workflow-arrow { color:var(--teal); font-size:1.4rem; }
.feature-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; margin:1rem 0; }
.limits-strip { padding:1rem 1.2rem; border-radius:12px; background:#edf1ef; color:var(--ink); margin:1.5rem 0; font-size:.9rem; }
.completeness-fill { display:block; height:8px; background:var(--teal); transform-origin:left; }
@media (prefers-reduced-motion: no-preference) {
  @keyframes enter-view { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
  @keyframes fill-bar { from { transform:scaleX(0); } to { transform:scaleX(1); } }
  .workflow-card,.feature-card,[data-testid="stMetric"] { animation:enter-view .35s ease both; transition:transform .18s ease; }
  .workflow-card:hover,.feature-card:hover { transform:translateY(-3px); }
  .completeness-fill { animation:fill-bar .6s ease both; }
}
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after { animation:none !important; transition:none !important; }
}
@media (max-width: 520px) {
  .stApp { font-size: 15px; }
  .block-container { padding:1.4rem 1rem 5rem; }
  h1 { font-size:2rem; }
  h2 { font-size:1.4rem; margin-top:2rem; }
  [data-testid="stMetric"] { padding:10px; }
  [data-testid="stHorizontalBlock"] { flex-direction:column; gap:1rem; }
  [data-testid="stHorizontalBlock"] > [data-testid="column"], [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { width:100% !important; flex:1 1 100% !important; }
  .workflow-grid,.feature-grid { grid-template-columns:1fr; }
  .workflow-arrow { justify-self:center; transform:rotate(90deg); }
  .hero-copy { font-size:1.12rem; }
  .demo-footer { font-size:.7rem; }
}
</style>
""", unsafe_allow_html=True)

def render_chart_summary(summary):
    st.markdown(
        f'<div class="chart-summary">{escape(summary)}'
        '<span class="chart-summary-label">Auto-generated from the data shown</span></div>',
        unsafe_allow_html=True,
    )

def plain_words(text):
    st.markdown(f'<p class="plain-words"><b>In plain words:</b> {escape(text)}</p>',unsafe_allow_html=True)


def render_workflow():
    cards=[
        ("Synthetic patients","Generated cycle histories and wearable-style observations."),
        ("Fitted model by sensor tier","Train on patients, calibrate and choose thresholds on validation."),
        ("Safe alert",f"Abstains on look-alikes; max {alert_limit} alert per cycle in the demo."),
    ]
    body='<span class="workflow-arrow" aria-hidden="true">→</span>'.join(
        f'<div class="workflow-card"><strong>{escape(title)}</strong><p>{escape(text)}</p></div>'
        for title,text in cards)
    st.markdown(f'<div class="workflow-grid">{body}</div>',unsafe_allow_html=True)
    plain_words("Compare inputs, inspect uncertainty, and see when the demo withholds a score.")
    st.caption("The dashboard loads the persisted fitted synthetic pipeline, including its validation-selected fallback and threshold. The separate twin remains illustrative.")


st.markdown(f'<div class="demo-footer"><a href="https://github.com/kushagragupta2005/CycleTwin_VIT" target="_blank" rel="noopener noreferrer">GitHub · CycleTwin_VIT</a>{escape(DISCLAIMER)} · Decision-support research prototype. This screen does not validate a clinical forecast.</div>',unsafe_allow_html=True)

@st.cache_data
def benchmark_metrics(claims_mtime):
    return load_claims()["development"]

claims=load_claims()
benchmark = benchmark_metrics(Path("docs/claims.json").stat().st_mtime_ns)
metric_keys=next(iter(benchmark["seeds"].values()))["metrics"]
forecast_days=sorted({int(key.split("_")[1]) for key in metric_keys})
all_tiers=sorted({int(key.rsplit("_",1)[1]) for key in metric_keys})
sensor_tiers=[tier for tier in all_tiers if "EHR" not in metric_keys[f"day_{forecast_days[-1]}_tier_{tier}"]["tier_name"]]
benchmark_day=forecast_days[-1]
alert_threshold,alert_limit=apply_alert_budget.__defaults__
benchmark_summary=[]
for day in forecast_days:
    for tier in all_tiers:
        seed_metrics=[seed["metrics"][f"day_{day}_tier_{tier}"] for seed in benchmark["seeds"].values()]
        benchmark_summary.append({
            "Forecast day":day,"Tier":tier,"Inputs":seed_metrics[0]["tier_name"],
            "Mean AUROC":float(np.mean([m["auroc"] for m in seed_metrics])),
            "Mean Brier":float(np.mean([m["brier"] for m in seed_metrics])),
            "Held-out cycles":sum(m["n_cycles"] for m in seed_metrics),
            "Seeds retaining candidate":sum(m["validation_selected_feature_tier"]==tier for m in seed_metrics),
        })
overview_summary=claims["frozen_summary"] or benchmark_summary
best_sensor=next(r for r in overview_summary if r["Forecast day"]==benchmark_day and r["Tier"]==sensor_tiers[-1])

@st.cache_data
def demo_cohort():
    return [r for r in attach_prior_cycle_lengths(generate(223,patients=36,cycles=2)) if r["cycle"] == 1]

cohort=demo_cohort()

guided_steps=(
    ("p0000",sensor_tiers[-1],"Notice the temperature trace, missing nights and the uncertainty band; the score uses the persisted fitted synthetic model."),
    ("p0026",sensor_tiers[-1],"Notice why this record is withheld: the abstain banner names the rule that fired."),
    ("p0002",sensor_tiers[0],"Notice the alert budget: add this eligible synthetic record to the alert log, then try adding it again."),
)

def select_guided_step(index):
    suffix,tier,_=guided_steps[index]
    st.session_state.update(
        view="Patient",guided=True,guided_step=index,display_tier=tier,
        patient_choice=next(r["patient"] for r in cohort if r["patient"].endswith(suffix)),
    )

def start_guided_demo():
    select_guided_step(0)

def leave_guided_demo():
    st.session_state["guided"]=False

page=st.segmented_control("Navigate",["Overview","Cohort","Patient","Method","Meet Kushi"],default="Overview",
                          key="view",on_change=leave_guided_demo) or "Overview"
st.markdown('<span class="synthetic-badge">Synthetic data only</span>',unsafe_allow_html=True)
st.sidebar.header("CycleTwin demo")
with st.sidebar.expander("Data source"):
    plain_words("Parse a synthetic Apple Health-shaped export locally. The scored cohort remains generated.")
    if st.button("Load synthetic Apple Health export"):
        subprocess.run([sys.executable,"scripts/make_synthetic_apple_export.py"],check=True,capture_output=True)
        st.session_state["apple_loaded"]=True
    export_path=Path("apple_health_export/export.xml")
    if st.session_state.get("apple_loaded") and export_path.exists():
        parsed=parse_export(export_path)
        st.caption(f"Synthetic XML parsed: {len(parsed['daily'])} dates")
    uploaded=st.file_uploader("Or upload a synthetic export XML",type=["xml"])
    if uploaded:
        parsed=parse_upload_bytes(uploaded.getvalue())
        st.caption(f"Parsed {len(parsed['daily'])} dates · cycle starts: {len(parsed['cycle_starts'])}")

display_controls=st.sidebar.expander("Display",expanded=page in ("Cohort","Patient"))
with display_controls:
    plain_words("Choose which synthetic record and sensor tier to inspect.")
    display_tier=st.selectbox("Display synthetic tier",all_tiers,index=all_tiers.index(sensor_tiers[-1]),
                             format_func=lambda t:f"Tier {t}"+(" · oracle-adjacent EHR-lite" if t not in sensor_tiers else ""),key="display_tier",on_change=leave_guided_demo)
    sort_by=st.selectbox("Sort synthetic list",["Risk", "Archetype", "Data completeness", "Tier"])
with st.sidebar.expander("About this demo"):
    plain_words("This receipt acknowledges a synthetic demonstration.")
    mock_consent=st.checkbox("I understand this screen uses synthetic records",value=False)
    if mock_consent:
        st.success("Mock consent receipt · synthetic demo · no real data")
    else:
        st.info("Select the mock consent receipt to explore the synthetic cohort.")
with st.sidebar.expander("Glossary"):
    plain_words("Definitions for the research terms used on screen.")
    st.markdown("**PMOS:** Polyendocrine metabolic ovarian syndrome; this generator includes synthetic PMOS archetypes.  \n**HOMA-IR:** A fasting-glucose-and-insulin-derived insulin-resistance estimate.  \n**Tier:** A feature set level used by the fitted benchmark.  \n**Abstain:** Withhold a score when a safety or data-quality rule fires.  \n**Conformal interval:** A data-calibrated range with marginal coverage on exchangeable data.")
st.sidebar.caption("Consent receipt and glossary apply to this synthetic demo only.")

rows=[]
for r in cohort:
    completeness=float(np.isfinite(r["temperature"][:14]).mean())
    flags=synthetic_safety_record(r,14)
    reasons=abstention_reasons(flags)
    output=predict(r,14,display_tier)
    risk=None if reasons else output["prob"]
    rows.append({"patient":r["patient"],"cycle":r["cycle"],"day":14,"phenotype":r["phenotype"],
                 "risk":risk,"abstain":bool(reasons),"reasons":reasons,"wear":completeness,
                 "record":r,"flags":flags,"ov_est":None if reasons else estimate_ovulation_day(r,14,output["selected_tier"]),
                 "prediction":output,"threshold":output["threshold"],"flag":False if reasons else output["flag"]})

sort_key={"Risk":lambda x:(-x["risk"] if x["risk"] is not None else float("inf"),x["patient"]), "Archetype":lambda x:(x["phenotype"],x["patient"]),
          "Data completeness":lambda x:(-x["wear"],x["patient"]), "Tier":lambda x:(display_tier,x["patient"])}[sort_by]
eligible=sorted(rows,key=sort_key)
with display_controls:
    selected_id=st.selectbox("Selected synthetic patient",[r["patient"] for r in eligible],key="patient_choice",on_change=leave_guided_demo)
item=next(r for r in eligible if r["patient"]==selected_id)
record=item["record"]
st.session_state["visible_prediction"]=safe_predict(record,14,display_tier,safety=item["flags"])
ix=int(item["patient"].split("p")[-1])
twin_repro=simulate_reproductive_axis(record["ir"],record["androgen"],seed=4000+ix)
page_title={"Overview":"CycleTwin", "Cohort":"Synthetic cohort", "Patient":f"Patient {selected_id}",
            "Method":"Model & methodology", "Meet Kushi":"Meet Kushi"}[page]
st.title(page_title)
if page!="Overview":
    st.caption(f"Tier {display_tier} · Synthetic demonstration")

if page=="Meet Kushi":
    render_kushi()
    st.stop()

if page=="Overview":
    st.markdown('<div class="hero-copy">Early warning of a missed or late-ovulation cycle for PMOS research, using synthetic wearable-style data.</div>',unsafe_allow_html=True)
    plain_words("Explore cycle history and wearable-style signals without measured hormone levels. This build demonstrates generated patterns, not a validated predictor for people with PMOS.")
    st.button("Try the demo",on_click=start_guided_demo,type="primary")
    render_workflow()
    stats=st.columns(4)
    stats[0].metric("Held-out cycles · synthetic",f"{best_sensor['Held-out cycles']:,}",
                    help="Test cycles summed once across seeds at the displayed forecast snapshot; repeated tiers and days are not counted again.")
    stats[1].metric("Seeds · synthetic",str(len((claims["frozen"] or benchmark)["seeds"])),
                    help="Independent random seeds for the same synthetic generator; these are not external clinical cohorts.")
    stats[2].metric("Mean AUROC · synthetic",f"{best_sensor['Mean AUROC']:.3f}",
                    help="Mean ranking metric across seeds for the described sensor tier. Higher ranks synthetic labels more accurately.")
    stats[3].metric("Mean Brier · synthetic",f"{best_sensor['Mean Brier']:.3f}",
                    help="Mean squared probability error across seeds for the described sensor tier. Lower is better within this simulator.")
    st.caption(f"Tier {best_sensor['Tier']} at forecast day {benchmark_day} · predeclared highest sensor tier. Frozen synthetic summary when available; older seeds are development evidence; calibration, feature fallback and thresholds were selected on validation, not test.")
    plain_words("These figures describe the fitted synthetic benchmark. They describe synthetic model performance, not clinical performance or individual confidence.")
    st.subheader("What makes it different")
    plain_words("The demonstration makes its safety rules, uncertainty and input limits visible.")
    features=[
        ("Look-alike abstention","Explicit rules withhold scores for thyroid, birth-control and early-menarche scenarios."),
        ("Alert budget",f"At most {alert_limit} synthetic alert per cycle; repeated log additions are blocked."),
        ("Conformal intervals","Illustrative marginal ranges, with coverage limits stated beside the chart."),
        ("Sensor tiers",f"Display tiers {', '.join(map(str,sensor_tiers))}; the additional EHR-lite benchmark is oracle-adjacent."),
        ("Apple Health-shaped import","A local synthetic XML parsing demonstration; imported files do not become scored cohort records."),
    ]
    cards="".join(f'<div class="feature-card"><strong>{escape(title)}</strong><p>{escape(text)}</p></div>' for title,text in features)
    st.markdown(f'<div class="feature-grid">{cards}</div>',unsafe_allow_html=True)
    st.markdown('<div class="feature-card"><strong>Twin demo · illustration, not used in the score</strong><p>Inspect coupled reproductive and metabolic simulator states alongside the separate forecast demonstration.</p></div>',unsafe_allow_html=True)
    plain_words("The twin is a visualization of assumed dynamics; it does not improve the evaluated number.")
    st.markdown('<div class="limits-strip"><b>Limits</b> · Synthetic only · Not validated · Not diagnosis</div>',unsafe_allow_html=True)
    plain_words("The generator creates the relationships the model learns. Reliable prediction without measured hormone levels has not been established in a real cohort.")
    st.stop()

if page == "Cohort":
    st.subheader("Risk-ranked synthetic cohort")
    plain_words("Compare generated records, see missing data, and find which explicit rules withhold a score.")
    with st.popover("ⓘ"):
        st.caption("“Not flagged” is neutral: it does not mean low clinical risk. The list is sortable through the sidebar.")
    summary=[]
    for r in eligible:
        state="Clinician review" if r["abstain"] else ("Flagged by validation cutoff" if r["flag"] else "Not flagged")
        summary.append({"Patient":r["patient"],"Synthetic archetype":r["phenotype"],"Fitted synthetic score":"Withheld" if r["abstain"] else round(r["risk"],3),
                        "Tier":f"Tier {display_tier}","Data completeness":round(r["wear"]*100),"Status":state,
                        "Metabolic axis":"CGM illustrative" if int(r["patient"].split("p")[-1])%4==0 else "Not sampled"})
    headers=["Patient","Synthetic archetype","Fitted synthetic score","Tier","Data completeness","Status","Metabolic axis"]
    table_rows=[]
    for row in summary:
        pct=row["Data completeness"]
        cells=[]
        for key in headers:
            if key=="Data completeness":
                continue
            if key=="Status":
                review=row[key]=="Clinician review"
                cls="status-review" if review else ("status-flagged" if row[key]=="Flagged by validation cutoff" else "status-neutral")
                cells.append(f'<td><span class="status-pill {cls}">{escape(str(row[key]))}</span></td>')
            elif key=="Fitted synthetic score":
                cells.append(f'<td title="Fitted synthetic model; not a diagnosis probability">{escape(str(row[key]))}</td>')
            else:
                cells.append(f'<td>{escape(str(row[key]))}</td>')
        cells.insert(4, f'<td><div style="display:flex;align-items:center;gap:8px"><span style="width:92px;height:8px;background:#e5eeeb;border-radius:8px;overflow:hidden"><span class="completeness-fill" style="width:{pct}%"></span></span><span>{pct}%</span></div></td>')
        table_rows.append("<tr>"+"".join(cells)+"</tr>")
    table_html='<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;background:#fff;color:#18313d;font-size:.88rem"><thead><tr>'+"".join(f'<th style="text-align:left;padding:10px;border-bottom:2px solid #d7e2e1">{escape(h)}</th>' for h in headers)+'</tr></thead><tbody>'+"".join(table_rows)+"</tbody></table></div>"
    st.markdown(table_html,unsafe_allow_html=True)
    model_rows=[item["prediction"]["metrics"]]
    mean_brier=float(np.mean([metric["brier"] for metric in model_rows]))
    mean_auroc=float(np.mean([metric["auroc"] for metric in model_rows]))
    st.caption(f"Fitted synthetic seed {item['prediction']['seed']} · requested Tier {display_tier}; selected Tier {item['prediction']['selected_tier']} · validation threshold {item['threshold']:.6f} · AUROC {mean_auroc:.3f} · Brier {mean_brier:.3f}. Not a diagnosis probability.")
    st.subheader("Interactive synthetic risk–coverage diagnostic")
    plain_words("As more non-abstaining records are included, compare the covered share and the share of incorrect demo labels.")
    with st.popover("ⓘ Diagnostic caveat"):
        st.caption("Diagnostic on this small generated cohort only; not a held-out evaluation result.")
    st.metric("Abstention rate",f"{np.mean([r['abstain'] for r in rows]):.0%}",help="Share of this generated display cohort for which an explicit safety or completeness rule withholds the score.")
    available=sorted([r for r in rows if not r["abstain"]],key=lambda r:max(r["risk"],1-r["risk"]),reverse=True)
    cover=[]; selective_error=[]
    for fraction in np.linspace(.1,1,10):
        count=max(1,int(len(available)*fraction)); chosen=available[:count]
        cover.append(count/max(len(rows),1))
        selective_error.append(float(np.mean([r["flag"]!=bool(r["record"]["event"]) for r in chosen])))
    st.line_chart({"coverage of all records":cover,"selective error":selective_error},color=["#0e766e","#65757b"])
    if cover and selective_error:
        render_chart_summary(
            f"Across the displayed sweep, coverage ranges from {min(cover):.0%} to {max(cover):.0%}; "
            f"selective error ranges from {min(selective_error):.0%} to {max(selective_error):.0%}."
        )
    st.stop()

if page == "Method":
    render_workflow()
    if claims["frozen"] is not None:
        st.subheader("Frozen synthetic evaluation")
        st.dataframe(pd.DataFrame(claims["frozen_summary"]),hide_index=True,use_container_width=True)
        st.caption("The frozen-v1 tag predates the guarded reserved-seed run. No clinical or external validation is implied.")
    st.subheader("Development evaluation results")
    plain_words("Read fitted-model performance by input tier and forecast day. All outcomes and inputs are generated.")
    with st.popover("ⓘ Benchmark caveat"):
        st.caption("Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")
    st.markdown("The dashboard uses persisted seed-97 fitted synthetic models and their validation-selected thresholds. The benchmark is not a clinical model.")
    model_rows=[seed["metrics"][f"day_{benchmark_day}_tier_{display_tier}"] for seed in benchmark["seeds"].values()]
    st.caption(f"Selected Tier {display_tier} · forecast day {benchmark_day} · synthetic held-out results")
    st.metric("Fitted benchmark AUROC",f"{np.mean([m['auroc'] for m in model_rows]):.3f}",help="Mean AUROC across synthetic held-out seeds for the selected tier and displayed forecast day; it is not a clinical accuracy estimate.")
    st.metric("Fitted benchmark Brier",f"{np.mean([m['brier'] for m in model_rows]):.3f}",help="Mean squared probability error across synthetic held-out seeds for the selected tier. Lower is better.")
    st.subheader("Sensor-tier comparison")
    plain_words("Matching rows can reflect a validation-selected calendar fallback. EHR-lite includes simulator internals and is oracle-adjacent.")
    st.dataframe(pd.DataFrame(benchmark_summary),hide_index=True,use_container_width=True)
    st.subheader("Selected-tier seed details")
    plain_words("The confidence intervals resample patients; cycles from a patient stay together.")
    st.dataframe(pd.DataFrame([{"Seed":seed,"AUROC":round(metric["auroc"],3),
                                "AUROC 95% CI":f"{metric['auroc_cluster_bootstrap_95ci'][0]:.3f}–{metric['auroc_cluster_bootstrap_95ci'][1]:.3f}",
                                "Brier":round(metric["brier"],3),"Held-out cycles":metric["n_cycles"]}
                               for seed,metric in zip(benchmark["seeds"].keys(),model_rows)]),hide_index=True,use_container_width=True)
    st.caption("These synthetic benchmark figures describe fitted models. They do not establish clinical validity or confidence for an individual record.")
    st.caption("Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")
    st.markdown("**Method:** synthetic generator → tiered fitted benchmark → held-out evaluation. The dashboard uses the fitted classifier; the simplified twin remains a separate illustration; the twin state is not used in the benchmark score.")
    render_reporting(claims,display_tier)
    render_alert_policy(claims)
    render_robustness(claims)
    render_bayesian_twin(claims)
    st.subheader("Honest limitations")
    plain_words("The software learns patterns created by its own simulator. It has not established reliable forecasting for people with PMOS without measured hormone levels.")
    st.markdown("- Synthetic data only; no clinical or external validation.\n- Patient panels use persisted fitted models; the generated display cohort is separate from training.\n- EHR-lite is oracle-adjacent because internal variables also influence generated labels.\n- Conformal and abstention coverage, and CGM forecasts, are not evaluated benchmark endpoints.\n- Twin dynamics are illustrative and unused by the fitted score; the input-editing sandbox is not an intervention model.\n- The displayed timeline includes later generated nights; prospective benchmark features are truncated at the forecast day.")
    st.stop()

st.divider()
if st.session_state.get("guided",False):
    step_index=st.session_state.get("guided_step",0)
    st.subheader("Guided demo")
    st.caption(f"Step {step_index+1} of {len(guided_steps)} · {selected_id} · Tier {display_tier}")
    plain_words(guided_steps[step_index][2])
    back,next_step=st.columns(2)
    back.button("Back",on_click=select_guided_step,args=(step_index-1,),disabled=step_index==0)
    next_step.button("Next",on_click=select_guided_step,args=(step_index+1,),disabled=step_index==len(guided_steps)-1)
    st.progress((step_index+1)/len(guided_steps),text="Guided demo progress")

model_rows=[item["prediction"]["metrics"]]
mean_brier=float(np.mean([metric["brier"] for metric in model_rows]))
mean_auroc=float(np.mean([metric["auroc"] for metric in model_rows]))
auroc_low=min(metric["auroc_cluster_bootstrap_95ci"][0] for metric in model_rows)
auroc_high=max(metric["auroc_cluster_bootstrap_95ci"][1] for metric in model_rows)
with st.expander(f"Model card · fitted benchmark Tier {display_tier}"):
    plain_words("These seed-level benchmark results provide context; they do not clinically validate this generated record.")
    st.caption("These synthetic benchmark figures describe fitted models. They do not establish clinical validity or confidence for an individual record.")
    st.dataframe(pd.DataFrame([{"Seed":seed, "AUROC":round(metric["auroc"],3), "AUROC 95% CI":f"{metric['auroc_cluster_bootstrap_95ci'][0]:.3f}–{metric['auroc_cluster_bootstrap_95ci'][1]:.3f}",
                                "Brier":round(metric["brier"],3), "Held-out cycles":metric["n_cycles"]}
                       for seed,metric in zip([str(item["prediction"]["seed"])],model_rows)]),hide_index=True,use_container_width=True)
    st.caption("Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")

if item["prediction"]["fallback_used"]:
    st.info("Calendar fallback selected · validation did not support retaining the richer feature set.")
st.subheader("Cycle overview")
plain_words("Inspect an individual generated cycle, its uncertainty and the rule behind any withheld score.")
with st.popover("ⓘ Patient caveats"):
    st.caption("These synthetic benchmark figures describe fitted models. They do not establish clinical validity or confidence for an individual record. Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")
if item["abstain"]:
    st.markdown('<div class="abstain-card">⏸ <b>Abstain · clinician review</b><br>Rule fired: '+"; ".join(item["reasons"])+"</div>",unsafe_allow_html=True)
    st.metric("Ovulation-delay axis","Withheld",help="Safety gate: no personal score, interval, explanation, sandbox or alert is available.")
    st.caption("No risk score shown because an abstention rule fired. Personal intervals, feature explanations and assumption-sandbox outputs are withheld; alerts are blocked.")
    st.subheader("Observed synthetic data only")
    st.line_chart(pd.DataFrame({"Temperature offset (°C)":record["temperature"][:14]}))
    st.stop()

left,right=st.columns([1.2,1])
with left:
    st.subheader(f"Patient {item['patient']} · cycle {item['cycle']+1}")
    if item["abstain"]:
        st.markdown('<div class="abstain-card">⏸ <b>Abstain · clinician review</b><br>Rule fired: '+"; ".join(item["reasons"])+"</div>",unsafe_allow_html=True)
    else:
        st.metric("Fitted synthetic E1 probability",f"{item['risk']:.0%}",help="Persisted fitted-model probability of the generated late/absent label. Synthetic-only, not a diagnosis probability.")
        st.caption(f"This synthetic model · Brier {mean_brier:.3f}; AUROC {mean_auroc:.3f} (patient-bootstrap 95% CI {auroc_low:.3f}–{auroc_high:.3f}); validation threshold {item['threshold']:.6f}. Not an individual confidence guarantee.")
        if not item["flag"]:
            st.markdown('<div class="cycletwin-neutral">Not flagged by the validation-selected cutoff. This is a neutral state, not a clinical reassurance.</div>',unsafe_allow_html=True)
        else:
            st.info("Flagged by the validation-selected synthetic cutoff; clinician interpretation would be required.")
    bounds=uncertainty(record,14,display_tier,item["prediction"])
    label_set=bounds["class_set"]
    est=bounds["estimate"]
    interval=bounds["interval"]
    st.write(f"Synthetic ovulation-day estimate: day {est}, marginal interval {interval[0]}–{interval[1]}.")
    plain_words("The band is an illustrative range around a heuristic day estimate; it does not guarantee an individual outcome.")
    st.caption(f"Split-conformal synthetic illustration · calibration seed {bounds['calibration']['seed']} · label set {label_set}. Day band conditional on ovulatory cycles; empirical coverage has not been evaluated. No individual guarantee.")
    temp=pd.DataFrame({"day":np.arange(1,29),"temperature_offset":record["temperature"][:28]})
    plain_words("The temperature line shows generated nightly offsets; crosses mark missing nights and the band shows the estimated day range.")
    missing=temp[temp["temperature_offset"].isna()].assign(marker=-0.18)
    ovulation_band=pd.DataFrame({"start":[interval[0]],"end":[interval[1]]})
    period=pd.DataFrame({"day":[1]})
    scale=alt.Scale(domain=[-0.25,0.35])
    band=alt.Chart(ovulation_band).mark_rect(color="#0e766e",opacity=.10).encode(x="start:Q",x2="end:Q",y=alt.value(0),y2=alt.value(270))
    trace=alt.Chart(temp.assign(segment=temp["temperature_offset"].isna().cumsum()).dropna()).mark_line(color="#0e766e",strokeWidth=2.5).encode(x=alt.X("day:Q",title="Cycle day"),y=alt.Y("temperature_offset:Q",title="Temperature offset (°C)",scale=scale),detail="segment:N")
    dots=alt.Chart(temp.dropna()).mark_circle(color="#0e766e",size=28).encode(x="day:Q",y=alt.Y("temperature_offset:Q",scale=scale))
    missing_marks=alt.Chart(missing).mark_point(shape="cross",color="#65757b",size=110).encode(x="day:Q",y=alt.Y("marker:Q",scale=scale))
    period_mark=alt.Chart(period).mark_rule(color="#b7791f",strokeDash=[4,3],strokeWidth=2).encode(x="day:Q")
    st.altair_chart((band+trace+dots+missing_marks+period_mark).properties(height=285),use_container_width=True)
    early=temp.loc[temp["day"]<=5,"temperature_offset"].dropna()
    late=temp.loc[temp["day"]>=21,"temperature_offset"].dropna()
    missing_n=int(temp["temperature_offset"].isna().sum())
    if not early.empty and not late.empty:
        early_mean=float(early.mean()); late_mean=float(late.mean())
        render_chart_summary(
            f"Mean temperature offset changed by {late_mean-early_mean:+.2f}°C from days 1–5 "
            f"({early_mean:+.2f}°C) to days 21–28 ({late_mean:+.2f}°C); "
            f"{missing_n} of 28 nights are missing."
        )
    else:
        render_chart_summary(f"{int(temp['temperature_offset'].notna().sum())} of 28 nightly values are observed; there are {missing_n} missing nights.")
    st.markdown('<div style="display:flex;gap:14px;flex-wrap:wrap;font-size:.82rem;color:#65757b"><span>🟩 Teal band · predicted ovulation interval</span><span>🟠 Amber dashed · assumed cycle start</span><span>✕ Gray cross · missing temperature</span></div>',unsafe_allow_html=True)
    st.caption("Missing nightly temperatures are not interpolated; lines break at missing nights. The period marker is assumed at plotted cycle day one, not read from an imported event.")
    st.subheader("Simplified twin state · not used in G1 score")
    plain_words("This changing simulator state illustrates assumed follicle growth. It is not used by the evaluated score.")
    twin_day=twin_repro["ovulation_day"]
    st.write(f"Twin ovulation-day state: {twin_day if twin_day>0 else 'no surge in simulation window'}")
    twin_days=pd.DataFrame({"cycle_day":np.arange(1,36),"follicle_state":twin_repro["follicle"][:35]})
    follicle_chart=alt.Chart(twin_days).mark_line(color="#0e766e",strokeWidth=2.5).encode(
        x=alt.X("cycle_day:Q",title="Cycle day",scale=alt.Scale(domain=[0,35],nice=False)),
        y=alt.Y("follicle_state:Q",title="Follicle state (simulated units)"),
        tooltip=[alt.Tooltip("cycle_day:Q",title="Cycle day"),alt.Tooltip("follicle_state:Q",title="Follicle state",format=".3f")])
    lh_threshold=alt.Chart(pd.DataFrame({"threshold":[TwinParameters().lh_threshold]})).mark_rule(color="#b7791f",strokeDash=[5,4]).encode(y="threshold:Q")
    st.altair_chart((follicle_chart+lh_threshold).properties(title="Twin follicle growth trajectory",height=220),use_container_width=True)
    peak_index=int(np.argmax(twin_days["follicle_state"].to_numpy()))
    follicle_min=float(twin_days["follicle_state"].min())
    follicle_max=float(twin_days["follicle_state"].max())
    render_chart_summary(
        f"Simulated follicle state ranged from {follicle_min:.2f} to {follicle_max:.2f} units, "
        f"with its highest plotted value on cycle day {int(twin_days.iloc[peak_index]['cycle_day'])}."
    )
    st.caption("Day-by-day simulated follicle state; dashed amber rule marks the LH threshold. Ovulation day above is the resulting scalar event.")
    st.caption("Shared synthetic insulin-resistance latent drives both axes. Coupling sweep: "+str(coupling_sweep(record["ir"],record["androgen"])))
    st.subheader("Exact fitted feature evidence")
    st.caption("Coefficient × standardized input, with imputation shown. Calibrated-logit contributions plus the calibrated intercept reproduce the fitted probability. Association, not causation.")
    st.dataframe(pd.DataFrame(item["prediction"]["contributions"]),hide_index=True,use_container_width=True)
with right:
    st.subheader("Two-axis risk view")
    plain_words("The cycle score and the glucose illustration describe separate synthetic signals.")
    if item["abstain"]:
        st.metric("Ovulation-delay axis","Withheld",help="An explicit abstention rule fired for this generated record; the score is withheld.")
        st.caption("No risk score shown because an abstention rule fired.")
    else:
        st.metric("Ovulation-delay axis",f"{item['risk']:.0%}",help="The same fitted synthetic probability shown in the cycle panel. Not a diagnosis probability.")
        st.caption(f"This synthetic model · Brier {mean_brier:.3f}; AUROC {mean_auroc:.3f} (patient-bootstrap 95% CI {auroc_low:.3f}–{auroc_high:.3f}); validation threshold {item['threshold']:.6f}. Not an individual confidence guarantee.")
    if ix%4==0:
        plain_words("The glucose line is simulated. The meal-window count reports threshold crossings in the full generated stream.")
        metabolic=simulate_metabolic_axis(record["ir"],twin_day,seed=3000+ix)
        glucose=metabolic["glucose_mg_dl"]; meals=metabolic["meal_indices"]
        meal_excursions=[excursion_event(glucose,m) for m in meals]
        g_risk=float(np.mean(meal_excursions))
        st.metric("Simulated meals with >140 mg/dL in 120 min",f"{g_risk:.0%}",help="Share of generated meal windows with a glucose value above the displayed reference within the post-meal horizon. Not a validated glucose forecast.")
        cgm=glucose[::8]
        cgm_df=pd.DataFrame({"minutes":np.arange(len(cgm))*metabolic["step_minutes"]*8,"glucose_mg_dl":cgm})
        cgm_line=alt.Chart(cgm_df).mark_line(color="#0e766e").encode(x=alt.X("minutes:Q",title="Elapsed time (minutes)"),y=alt.Y("glucose_mg_dl:Q",title="Glucose (mg/dL)"),tooltip=["minutes:Q","glucose_mg_dl:Q"])
        cgm_threshold=alt.Chart(pd.DataFrame({"threshold":[140]})).mark_rule(color="#b7791f",strokeDash=[5,4]).encode(y="threshold:Q")
        st.altair_chart((cgm_line+cgm_threshold).properties(title=f"Synthetic CGM · plotted every {metabolic['step_minutes']*8} minutes",height=250),use_container_width=True)
        render_chart_summary(
            f"Simulated glucose exceeded 140 mg/dL within 120 minutes after "
            f"{sum(meal_excursions)} of {len(meal_excursions)} meal windows."
        )
        with st.popover("ⓘ CGM caveat"):
            st.caption("15-minute synthetic values · two adjacent 14-day windows · not clinically evaluated")
    else:
        st.metric("Glycaemic-excursion proxy","Not sampled",help="This generated patient has no CGM panel selected for the display demonstration.")
    st.progress(item["wear"],text=f"Nightly temperature completeness {item['wear']:.0%}")

with st.container(border=True):
    st.subheader("Assumption sandbox · synthetic input editing")
    plain_words("Edit an invented input and rerun the fitted classifier. This is not an intervention forecast or expected health benefit.")
    with st.popover("ⓘ What-if caveat"):
        st.caption("Illustrative assumptions, not a treatment recommendation. No intervention effect is clinically established.")
    history=np.asarray(record["prior_cycle_lengths"],dtype=float)
    edited=st.number_input("Invented prior-cycle mean (days)",min_value=float(np.min([r["cycle_length"] for r in cohort])),
                           max_value=float(np.max([r["cycle_length"] for r in cohort])),value=float(np.mean(history)))
    if st.button("Run synthetic assumption sandbox"):
        altered=dict(record,prior_cycle_lengths=[edited]*len(history))
        sandbox=predict(altered,14,display_tier)
        st.write(f"Edited synthetic-input probability: {sandbox['prob']:.1%}; validation threshold {sandbox['threshold']:.6f}. This is not a treatment recommendation.")
        st.caption("No lifestyle multiplier or causal intervention model is used. This edits assumed historical data only.")

with st.container(border=True):
    st.subheader("Synthetic alert log")
    plain_words("Add an eligible generated alert and inspect the per-cycle budget. Repeated additions do not create duplicate entries.")
    with st.popover("ⓘ Alert-log caveat"):
        st.caption("The first eligible day 10/14/18 threshold crossing is retained; later scores cannot replace it. At most one alert per synthetic patient-cycle. Explanations are templated from state and feature contributions; no LLM is used in the loop.")
    predictions=[]
    for r in rows:
        if r["abstain"]:
            continue
        for day in (10,14,18):
            predictions.append({"patient":r["patient"],"cycle":r["cycle"],"day":day,
                                "risk":predict(r["record"],day,display_tier)["prob"],
                                "threshold":predict(r["record"],day,display_tier)["threshold"],"abstain":bool(abstention_reasons(synthetic_safety_record(r["record"],day)))})
    budgeted=apply_sequential_alert_policy(predictions,max_per_cycle=alert_limit)
    if st.button("Add selected synthetic alert to log"):
        chosen=next((r for r in budgeted if r["patient"]==item["patient"] and r["cycle"]==item["cycle"] and r["alert"]),None)
        existing=st.session_state.setdefault("alert_log",[])
        if chosen and not any(x["patient"]==item["patient"] and x["cycle"]==item["cycle"] for x in existing):
            existing.append({"patient":item["patient"],"cycle":item["cycle"],"day":chosen["day"],"risk":chosen["risk"]})
        elif not chosen:
            st.warning("No alert was selected for this synthetic patient-cycle under the current budget.")
        else:
            st.info("This synthetic patient-cycle is already in the one-alert log.")
    st.write(st.session_state.get("alert_log",[]))
