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
from src.model import forecast, estimate_ovulation_day
from src.safety import abstention_reasons
from src.conformal import calibrate_binary, calibrate_ovulation_interval, classification_set, ovulation_interval
from src.alerts import apply_alert_budget
from src.explanations import explain_state
from src.metabolic import excursion_event
from src.twin import simulate_reproductive_axis, simulate_metabolic_axis, coupling_sweep, TwinParameters
from src.adapters.apple_health import parse_export

DISCLAIMER="Not for diagnosis, contraception or conception planning. Synthetic demonstration only."
st.set_page_config(page_title="CycleTwin synthetic demo", layout="wide")
st.markdown("""
<style>
:root { --ink:#18313d; --muted:#5f717b; --teal:#0e766e; --teal-soft:#e8f4f1; --amber:#b7791f; --amber-soft:#fff7e6; --rose:#9a5d63; --rose-soft:#faeeee; --line:#d7e2e1; }
.stApp { background: #f7faf9; color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
h1, h2, h3 { color: var(--ink); letter-spacing: -0.02em; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:12px; padding:14px; }
[data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricValue"], [data-testid="stMetric"] [data-testid="stMetricDelta"] { color:var(--ink) !important; }
.cycletwin-note { color:var(--muted); font-size:0.86rem; }
.cycletwin-neutral { color:var(--muted); font-size:0.86rem; }
input[type="range"] { accent-color: var(--teal); }
.abstain-card { border:1px solid var(--amber); background:var(--amber-soft); border-radius:12px; padding:12px 14px; color:var(--ink); }
.status-pill { display:inline-block; border-radius:999px; padding:3px 9px; font-size:.82rem; white-space:nowrap; }
.status-neutral { background:#edf1f2; color:#52616a; }
.status-review { background:#fff0cf; color:#77500a; }
.status-flagged { background:#e5f3f0; color:#175d56; }
.demo-footer { position:fixed; z-index:999; left:0; right:0; bottom:0; padding:8px 1rem; background:#18313d; color:#fff; text-align:center; font-size:.82rem; }
.block-container { padding-bottom:3.5rem; }
@media (max-width: 520px) {
  .stApp { font-size: 15px; }
  [data-testid="stMetric"] { padding:10px; }
  [data-testid="stHorizontalBlock"] { flex-direction:column; gap:1rem; }
  [data-testid="stHorizontalBlock"] > [data-testid="column"] { width:100% !important; flex:1 1 100% !important; }
}
</style>
""", unsafe_allow_html=True)
st.title("CycleTwin · synthetic cycle monitor")
st.markdown(f'<div class="demo-footer">{escape(DISCLAIMER)} · Decision-support research prototype. This screen does not validate a clinical forecast.</div>',unsafe_allow_html=True)

@st.cache_data
def benchmark_metrics():
    return json.loads(Path("results.json").read_text())

benchmark = benchmark_metrics()

@st.cache_data
def demo_cohort():
    cohort=generate(223,patients=36,cycles=1)
    calibration=generate(211,patients=240,cycles=1)
    probs=[forecast(r,14,2) for r in calibration]
    labels=[r["event"] for r in calibration]
    q_cls=calibrate_binary(labels,probs)
    observed=[r for r in calibration if r["ovulation_day"]>0]
    estimates=[estimate_ovulation_day(r,14,2) for r in observed]
    q_ov=calibrate_ovulation_interval([r["ovulation_day"] for r in observed],estimates)
    return cohort,q_cls,q_ov

cohort,q_cls,q_ov=demo_cohort()
st.sidebar.header("CycleTwin demo")
page=st.sidebar.radio("Navigate",["Cohort list","Patient view","Model & methodology"],key="page")
st.sidebar.subheader("Data source")
if st.sidebar.button("Load synthetic Apple Health export"):
    subprocess.run([sys.executable,"scripts/make_synthetic_apple_export.py"],check=True,capture_output=True)
    st.session_state["apple_loaded"]=True

export_path=Path("apple_health_export/export.xml")
if st.session_state.get("apple_loaded") and export_path.exists():
    parsed=parse_export(export_path)
    st.sidebar.caption(f"Synthetic XML parsed: {len(parsed['daily'])} dates")
uploaded=st.sidebar.file_uploader("Or upload a synthetic export XML",type=["xml"])
if uploaded:
    p=Path("/tmp/cycletwin_synthetic_upload.xml"); p.write_bytes(uploaded.getvalue())
    parsed=parse_export(p)
    st.sidebar.caption(f"Parsed {len(parsed['daily'])} dates · cycle starts: {len(parsed['cycle_starts'])}")

st.sidebar.subheader("Display")
display_tier=st.sidebar.selectbox("Display synthetic tier",[0,1,2],index=2,
                                  format_func=lambda t:f"Tier {t}")
sort_by=st.sidebar.selectbox("Sort synthetic list",["Risk", "Archetype", "Data completeness", "Tier"])
st.sidebar.subheader("About this demo")
mock_consent=st.sidebar.checkbox("I understand this screen uses synthetic records",value=False)
if mock_consent:
    st.sidebar.success("Mock consent receipt · synthetic demo · no real data")
else:
    st.sidebar.info("Select the mock consent receipt to explore the synthetic cohort.")
with st.sidebar.expander("Glossary"):
    st.markdown("**PMOS:** Polyendocrine metabolic ovarian syndrome; this generator includes synthetic PMOS archetypes.  \n**HOMA-IR:** A fasting-glucose-and-insulin-derived insulin-resistance estimate.  \n**Tier:** A feature set level used by the fitted benchmark.  \n**Abstain:** Withhold a score when a safety or data-quality rule fires.  \n**Conformal interval:** A data-calibrated range with marginal coverage on exchangeable data.")
st.sidebar.caption("Consent receipt and glossary apply to this synthetic demo only.")

rows=[]
for r in cohort:
    completeness=float(np.isfinite(r["temperature"][:14]).mean())
    age=17 if r["phenotype"]=="early_menarche" else 29
    flags={"age":age,"early_post_menarche":r["phenotype"]=="early_menarche",
           "tsh_abnormal":r["phenotype"]=="thyroid_mimic","prolactin_abnormal":False,
           "hormonal_contraception":r["phenotype"]=="contraception","pregnant":False,
           "postpartum":False,"breastfeeding":False,"perimenopausal":False,
           "wear_completeness":completeness}
    reasons=abstention_reasons(flags)
    risk=forecast(r,14,2)
    rows.append({"patient":r["patient"],"cycle":r["cycle"],"day":14,"phenotype":r["phenotype"],
                 "risk":risk,"abstain":bool(reasons),"reasons":reasons,"wear":completeness,
                 "record":r,"flags":flags,"ov_est":estimate_ovulation_day(r,14,2)})

for row in rows:
    row["risk"]=forecast(row["record"],14,display_tier)
sort_key={"Risk":lambda x:(-x["risk"],x["patient"]), "Archetype":lambda x:(x["phenotype"],x["patient"]),
          "Data completeness":lambda x:(-x["wear"],x["patient"]), "Tier":lambda x:(display_tier,x["patient"])}[sort_by]
eligible=sorted(rows,key=sort_key)
selected_id=st.sidebar.selectbox("Selected synthetic patient",[r["patient"] for r in eligible])
item=next(r for r in eligible if r["patient"]==selected_id)
record=item["record"]
ix=int(item["patient"].split("p")[-1])
twin_repro=simulate_reproductive_axis(record["ir"],record["androgen"],seed=4000+ix)

if page == "Cohort list":
    st.subheader("Risk-ranked synthetic cohort")
    with st.popover("ⓘ"):
        st.caption("“Not flagged” is neutral: it does not mean low clinical risk. The list is sortable through the sidebar.")
    summary=[]
    for r in eligible:
        state="Clinician review" if r["abstain"] else ("Flagged by demo cutoff" if r["risk"]>=.5 else "Not flagged")
        summary.append({"Patient":r["patient"],"Synthetic archetype":r["phenotype"],"Fixed demo score":round(r["risk"],3),
                        "Tier":f"Tier {display_tier}","Data completeness":round(r["wear"]*100),"Status":state,
                        "Metabolic axis":"CGM illustrative" if int(r["patient"].split("p")[-1])%4==0 else "Not sampled"})
    headers=["Patient","Synthetic archetype","Fixed demo score","Tier","Data completeness","Status","Metabolic axis"]
    table_rows=[]
    for row in summary:
        pct=row["Data completeness"]
        cells=[]
        for key in headers:
            if key=="Data completeness":
                continue
            if key=="Status":
                review=row[key]=="Clinician review"
                cls="status-review" if review else ("status-flagged" if row[key]=="Flagged by demo cutoff" else "status-neutral")
                cells.append(f'<td><span class="status-pill {cls}">{escape(str(row[key]))}</span></td>')
            elif key=="Fixed demo score":
                cells.append(f'<td title="Fixed synthetic heuristic; not a diagnosis probability">{escape(str(row[key]))}</td>')
            else:
                cells.append(f'<td>{escape(str(row[key]))}</td>')
        cells.insert(4, f'<td><div style="display:flex;align-items:center;gap:8px"><span style="width:92px;height:8px;background:#e5eeeb;border-radius:8px;overflow:hidden"><span style="display:block;width:{pct}%;height:8px;background:#0e766e"></span></span><span>{pct}%</span></div></td>')
        table_rows.append("<tr>"+"".join(cells)+"</tr>")
    table_html='<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;background:#fff;color:#18313d;font-size:.88rem"><thead><tr>'+"".join(f'<th style="text-align:left;padding:10px;border-bottom:2px solid #d7e2e1">{escape(h)}</th>' for h in headers)+'</tr></thead><tbody>'+"".join(table_rows)+"</tbody></table></div>"
    st.markdown(table_html,unsafe_allow_html=True)
    model_rows=[seed["metrics"][f"day_14_tier_{display_tier}"] for seed in benchmark["seeds"].values()]
    mean_brier=float(np.mean([metric["brier"] for metric in model_rows]))
    mean_auroc=float(np.mean([metric["auroc"] for metric in model_rows]))
    st.caption(f"Fixed synthetic demo score (not a diagnosis probability). Separate fitted benchmark Tier {display_tier}: AUROC {mean_auroc:.3f} · Brier {mean_brier:.3f}; see Model & methodology for intervals and seed-level results.")
    st.subheader("Interactive synthetic risk–coverage diagnostic")
    with st.popover("ⓘ Diagnostic caveat"):
        st.caption("Diagnostic on this small generated cohort only; not a held-out evaluation result.")
    st.metric("Abstention rate",f"{np.mean([r['abstain'] for r in rows]):.0%}")
    available=sorted([r for r in rows if not r["abstain"]],key=lambda r:max(r["risk"],1-r["risk"]),reverse=True)
    cover=[]; selective_error=[]
    for fraction in np.linspace(.1,1,10):
        count=max(1,int(len(available)*fraction)); chosen=available[:count]
        cover.append(count/max(len(rows),1))
        selective_error.append(float(np.mean([(r["risk"]>=.5)!=bool(r["record"]["event"]) for r in chosen])))
    st.line_chart({"coverage of all records":cover,"selective error":selective_error})
    st.stop()

if page == "Model & methodology":
    st.subheader("Model & methodology")
    with st.popover("ⓘ Benchmark caveat"):
        st.caption("Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")
    st.markdown("The dashboard's fixed synthetic demo score is a heuristic. The separately fitted benchmark is evaluated on held-out synthetic cycles; it is not a clinical model.")
    model_rows=[seed["metrics"][f"day_14_tier_{display_tier}"] for seed in benchmark["seeds"].values()]
    st.metric("Fitted benchmark AUROC",f"{np.mean([m['auroc'] for m in model_rows]):.3f}")
    st.metric("Fitted benchmark Brier",f"{np.mean([m['brier'] for m in model_rows]):.3f}")
    st.dataframe(pd.DataFrame([{"Seed":seed,"AUROC":round(metric["auroc"],3),
                                "AUROC 95% CI":f"{metric['auroc_cluster_bootstrap_95ci'][0]:.3f}–{metric['auroc_cluster_bootstrap_95ci'][1]:.3f}",
                                "Brier":round(metric["brier"],3),"Held-out cycles":metric["n_cycles"]}
                               for seed,metric in zip(benchmark["seeds"].keys(),model_rows)]),hide_index=True,use_container_width=True)
    st.caption("These figures belong to the separately fitted benchmark model, not the dashboard’s fixed synthetic demo score.")
    st.caption("Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")
    st.markdown("**Method:** synthetic generator → tiered fitted benchmark → held-out evaluation. The dashboard heuristic and the simplified twin are separate demonstrations; the twin state is not used in the benchmark score.")
    st.stop()

st.divider()

model_rows=[seed["metrics"][f"day_14_tier_{display_tier}"] for seed in benchmark["seeds"].values()]
mean_brier=float(np.mean([metric["brier"] for metric in model_rows]))
mean_auroc=float(np.mean([metric["auroc"] for metric in model_rows]))
auroc_low=min(metric["auroc_cluster_bootstrap_95ci"][0] for metric in model_rows)
auroc_high=max(metric["auroc_cluster_bootstrap_95ci"][1] for metric in model_rows)
with st.expander(f"Model card · fitted benchmark Tier {display_tier}"):
    st.caption("These figures belong to the separately fitted benchmark model, not the dashboard’s fixed synthetic demo score.")
    st.dataframe(pd.DataFrame([{"Seed":seed, "AUROC":round(metric["auroc"],3), "AUROC 95% CI":f"{metric['auroc_cluster_bootstrap_95ci'][0]:.3f}–{metric['auroc_cluster_bootstrap_95ci'][1]:.3f}",
                                "Brier":round(metric["brier"],3), "Held-out cycles":metric["n_cycles"]}
                       for seed,metric in zip(benchmark["seeds"].keys(),model_rows)]),hide_index=True,use_container_width=True)
    st.caption("Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")

st.subheader("Patient view")
with st.popover("ⓘ Patient caveats"):
    st.caption("These figures belong to the separately fitted benchmark model, not the dashboard’s fixed synthetic demo score. Synthetic held-out data only. Patient-cluster bootstrap confidence intervals; not clinical performance or a confidence guarantee for this record.")
left,right=st.columns([1.2,1])
with left:
    st.subheader(f"Patient {item['patient']} · cycle {item['cycle']+1}")
    if item["abstain"]:
        st.markdown('<div class="abstain-card">⏸ <b>Abstain · clinician review</b><br>Rule fired: '+"; ".join(item["reasons"])+"</div>",unsafe_allow_html=True)
    else:
        st.metric("Synthetic demo E1 score",f"{item['risk']:.0%}")
        st.caption(f"Separate fitted benchmark at day 14 · Brier {mean_brier:.3f}; AUROC {mean_auroc:.3f} (seed-level 95% CI span {auroc_low:.3f}–{auroc_high:.3f}). These do not calibrate this fixed demo score.")
        if item["risk"] < .5:
            st.markdown('<div class="cycletwin-neutral">Not flagged by the fixed demo cutoff. This is a neutral state, not a clinical reassurance.</div>',unsafe_allow_html=True)
        else:
            st.info("Flagged by the fixed synthetic demo cutoff; clinician interpretation would be required.")
    label_set=classification_set(item["risk"],q_cls)
    est=item["ov_est"]
    interval=ovulation_interval(est,q_ov)
    st.write(f"Synthetic ovulation-day estimate: day {est}, marginal interval {interval[0]}–{interval[1]}.")
    st.caption(f"Split-conformal illustration · calibration seed 211 · label set {label_set}; marginal coverage only, not conditional coverage.")
    temp=pd.DataFrame({"day":np.arange(1,29),"temperature_offset":record["temperature"][:28]})
    missing=temp[temp["temperature_offset"].isna()].assign(marker=-0.18)
    ovulation_band=pd.DataFrame({"start":[interval[0]],"end":[interval[1]]})
    period=pd.DataFrame({"day":[1]})
    scale=alt.Scale(domain=[-0.25,0.35])
    band=alt.Chart(ovulation_band).mark_rect(color="#0e766e",opacity=.10).encode(x="start:Q",x2="end:Q",y=alt.value(0),y2=alt.value(270))
    trace=alt.Chart(temp.dropna()).mark_line(color="#0e766e",strokeWidth=2.5).encode(x=alt.X("day:Q",title="Cycle day"),y=alt.Y("temperature_offset:Q",title="Temperature offset (°C)",scale=scale))
    dots=alt.Chart(temp.dropna()).mark_circle(color="#0e766e",size=28).encode(x="day:Q",y=alt.Y("temperature_offset:Q",scale=scale))
    missing_marks=alt.Chart(missing).mark_point(shape="cross",color="#9a5d63",size=110).encode(x="day:Q",y=alt.Y("marker:Q",scale=scale))
    period_mark=alt.Chart(period).mark_rule(color="#b7791f",strokeDash=[4,3],strokeWidth=2).encode(x="day:Q")
    st.altair_chart((band+trace+dots+missing_marks+period_mark).properties(height=285),use_container_width=True)
    st.markdown('<div style="display:flex;gap:14px;flex-wrap:wrap;font-size:.82rem;color:#5f717b"><span>🟩 Teal band · predicted ovulation interval</span><span>🟠 Amber dashed · logged period start</span><span>✕ Muted red · missing temperature</span></div>',unsafe_allow_html=True)
    st.caption("Missing nightly temperatures are not interpolated.")
    st.subheader("Simplified twin state · not used in G1 score")
    twin_day=twin_repro["ovulation_day"]
    st.write(f"Twin ovulation-day state: {twin_day if twin_day>0 else 'no surge in simulation window'}")
    twin_days=pd.DataFrame({"cycle_day":np.arange(1,36),"follicle_state":twin_repro["follicle"][:35]})
    follicle_chart=alt.Chart(twin_days).mark_line(color="#0e766e",strokeWidth=2.5).encode(
        x=alt.X("cycle_day:Q",title="Cycle day",scale=alt.Scale(domain=[0,35],nice=False)),
        y=alt.Y("follicle_state:Q",title="Follicle state (simulated units)"),
        tooltip=[alt.Tooltip("cycle_day:Q",title="Cycle day"),alt.Tooltip("follicle_state:Q",title="Follicle state",format=".3f")])
    lh_threshold=alt.Chart(pd.DataFrame({"threshold":[TwinParameters().lh_threshold]})).mark_rule(color="#b7791f",strokeDash=[5,4]).encode(y="threshold:Q")
    st.altair_chart((follicle_chart+lh_threshold).properties(title="Twin follicle growth trajectory",height=220),use_container_width=True)
    st.caption("Day-by-day simulated follicle state; dashed amber rule marks the LH threshold. Ovulation day above is the resulting scalar event.")
    st.caption("Shared synthetic insulin-resistance latent drives both axes. Coupling sweep: "+str(coupling_sweep(record["ir"],record["androgen"])))
    temp_effect=float(np.nanmean(record['temperature'][8:14])-np.nanmean(record['temperature'][:5]))
    st.write(explain_state({"ovulation_estimate":est},{"temperature_shift":temp_effect,"rhr_offset":float(np.nanmean(record['rhr'][:14]))}))
with right:
    st.subheader("Two-axis risk view")
    if item["abstain"]:
        st.metric("Ovulation-delay axis","Withheld")
        st.caption("No risk score shown because an abstention rule fired.")
    else:
        st.metric("Ovulation-delay axis",f"{item['risk']:.0%}")
        st.caption(f"Separate fitted benchmark at day 14 · Brier {mean_brier:.3f}; AUROC {mean_auroc:.3f} (seed-level 95% CI span {auroc_low:.3f}–{auroc_high:.3f}). These do not calibrate this fixed demo score.")
    if ix%4==0:
        metabolic=simulate_metabolic_axis(record["ir"],twin_day,seed=3000+ix)
        glucose=metabolic["glucose_mg_dl"]; meals=metabolic["meal_indices"]
        g_risk=float(np.mean([excursion_event(glucose,m) for m in meals]))
        st.metric("Simulated meals with >140 mg/dL in 120 min",f"{g_risk:.0%}")
        cgm=glucose[::8]
        cgm_df=pd.DataFrame({"minutes":np.arange(len(cgm))*metabolic["step_minutes"]*8,"glucose_mg_dl":cgm})
        cgm_line=alt.Chart(cgm_df).mark_line(color="#0e766e").encode(x=alt.X("minutes:Q",title="Elapsed time (minutes)"),y=alt.Y("glucose_mg_dl:Q",title="Glucose (mg/dL)"),tooltip=["minutes:Q","glucose_mg_dl:Q"])
        cgm_threshold=alt.Chart(pd.DataFrame({"threshold":[140]})).mark_rule(color="#b7791f",strokeDash=[5,4]).encode(y="threshold:Q")
        st.altair_chart((cgm_line+cgm_threshold).properties(title="Synthetic CGM · 15-minute samples",height=250),use_container_width=True)
        with st.popover("ⓘ CGM caveat"):
            st.caption("15-minute synthetic values · two adjacent 14-day windows · not clinically evaluated")
    else:
        st.metric("Glycaemic-excursion proxy","Not sampled")
    st.progress(item["wear"],text=f"Nightly temperature completeness {item['wear']:.0%}")

with st.container(border=True):
    st.subheader("Illustrative what-if ranges")
    with st.popover("ⓘ What-if caveat"):
        st.caption("Illustrative assumptions, not a treatment recommendation. No intervention effect is clinically established.")
    scenario=st.selectbox("Scenario",["Regular sleep","Daily walk","Lower-GI food swap","Lower evening stress","Illustrative weight change"])
    factors={"Regular sleep":(.80,.98),"Daily walk":(.75,.98),"Lower-GI food swap":(.80,1.00),"Lower evening stress":(.80,1.00),"Illustrative weight change":(.75,.98)}
    if st.button("Show illustrative range"):
        low,high=factors[scenario]
        st.write(f"Assumption-only range for demo E1 score: {item['risk']*low:.0%}–{item['risk']*high:.0%}. This is not a treatment recommendation.")

with st.container(border=True):
    st.subheader("Synthetic alert log")
    with st.popover("ⓘ Alert-log caveat"):
        st.caption("At most one alert per synthetic patient-cycle. Explanations are templated from state and feature contributions; no LLM is used in the loop.")
    predictions=[]
    for r in rows:
        for day in (10,14,18):
            predictions.append({"patient":r["patient"],"cycle":r["cycle"],"day":day,
                                "risk":forecast(r["record"],day,display_tier),"abstain":r["abstain"]})
    budgeted=apply_alert_budget(predictions,threshold=.50,max_per_cycle=1)
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
