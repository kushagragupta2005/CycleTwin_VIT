"""Local synthetic-data dashboard. No clinical workflow or personal export is used."""
from pathlib import Path
import subprocess
import sys
import numpy as np
import streamlit as st

from src.generator import generate
from src.model import forecast, estimate_ovulation_day
from src.safety import abstention_reasons
from src.conformal import calibrate_binary, calibrate_ovulation_interval, classification_set, ovulation_interval
from src.alerts import apply_alert_budget
from src.explanations import explain_state
from src.metabolic import excursion_event
from src.twin import simulate_reproductive_axis, simulate_metabolic_axis, coupling_sweep
from src.adapters.apple_health import parse_export

DISCLAIMER="Not for diagnosis, contraception or conception planning. Synthetic demonstration only."
st.set_page_config(page_title="CycleTwin synthetic demo", layout="wide")
st.title("CycleTwin · synthetic cycle monitor")
st.caption(DISCLAIMER)
st.caption("Decision-support research prototype. This screen does not validate a clinical forecast.")

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
st.sidebar.header("Synthetic demo")
mock_consent=st.sidebar.checkbox("I understand this screen uses synthetic records",value=False)
if mock_consent:
    st.sidebar.success("Mock consent receipt · synthetic demo · no real data")
else:
    st.sidebar.info("Select the mock consent receipt to explore the synthetic cohort.")

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

eligible=sorted(rows,key=lambda x:x["risk"],reverse=True)
st.subheader("Risk-ranked synthetic cohort")
summary=[{"Patient":r["patient"],"Synthetic phenotype":r["phenotype"],"E1 risk":round(r["risk"],3),
          "Metabolic axis":"CGM illustrative" if int(r["patient"].split("p")[-1])%4==0 else "CGM not sampled",
          "Tier":"Tier 2 · synthetic temperature","Completeness":round(r["wear"],2),
          "Status":"Clinician review" if r["abstain"] else "Forecast available"} for r in eligible]
st.dataframe(summary,use_container_width=True,hide_index=True)
st.subheader("Interactive synthetic risk–coverage diagnostic")
st.caption("Diagnostic on this small generated cohort only; not a held-out evaluation result.")
st.metric("Abstention rate",f"{np.mean([r['abstain'] for r in rows]):.0%}")
available=sorted([r for r in rows if not r["abstain"]],key=lambda r:max(r["risk"],1-r["risk"]),reverse=True)
cover=[]; selective_error=[]
for fraction in np.linspace(.1,1,10):
    count=max(1,int(len(available)*fraction)); chosen=available[:count]
    cover.append(count/max(len(rows),1))
    selective_error.append(float(np.mean([(r["risk"]>=.5)!=bool(r["record"]["event"]) for r in chosen])))
st.line_chart({"coverage of all records":cover,"selective error":selective_error})
selected_id=st.selectbox("Open synthetic patient",[r["patient"] for r in eligible])
item=next(r for r in eligible if r["patient"]==selected_id)
record=item["record"]
ix=int(item["patient"].split("p")[-1])
twin_repro=simulate_reproductive_axis(record["ir"],record["androgen"],seed=4000+ix)
st.divider()
left,right=st.columns([1.2,1])
with left:
    st.subheader(f"Patient {item['patient']} · cycle {item['cycle']+1}")
    if item["abstain"]:
        st.warning("Clinician review: consider other causes. " + "; ".join(item["reasons"]))
    else:
        st.metric("Synthetic E1 risk",f"{item['risk']:.0%}")
    label_set=classification_set(item["risk"],q_cls)
    est=item["ov_est"]
    interval=ovulation_interval(est,q_ov)
    st.write(f"Synthetic ovulation-day estimate: day {est}, marginal interval {interval[0]}–{interval[1]}.")
    st.caption(f"Split-conformal illustration · calibration seed 211 · label set {label_set}; marginal coverage only, not conditional coverage.")
    st.line_chart({"temperature offset":record["temperature"][:28]})
    st.subheader("Simplified twin state · not used in G1 score")
    twin_day=twin_repro["ovulation_day"]
    st.write(f"Twin ovulation-day state: {twin_day if twin_day>0 else 'no surge in simulation window'}")
    st.line_chart({"Twin temperature proxy (°C)":twin_repro["temperature_c"][:35]})
    st.caption("Shared synthetic insulin-resistance latent drives both axes. Coupling sweep: "+str(coupling_sweep(record["ir"],record["androgen"])))
    temp_effect=float(np.nanmean(record['temperature'][8:14])-np.nanmean(record['temperature'][:5]))
    st.write(explain_state({"ovulation_estimate":est},{"temperature_shift":temp_effect,"rhr_offset":float(np.nanmean(record['rhr'][:14]))}))
with right:
    st.subheader("Two-axis risk view")
    st.metric("Ovulation-delay axis",f"{item['risk']:.0%}")
    if ix%4==0:
        metabolic=simulate_metabolic_axis(record["ir"],twin_day,seed=3000+ix)
        glucose=metabolic["glucose_mg_dl"]; meals=metabolic["meal_indices"]
        g_risk=float(np.mean([excursion_event(glucose,m) for m in meals]))
        st.metric("Simulated meals with >140 mg/dL in 120 min",f"{g_risk:.0%}")
        st.line_chart({"Synthetic CGM (mg/dL)":glucose[::8]})
        st.caption("15-minute synthetic values · two adjacent 14-day windows · not clinically evaluated")
    else:
        st.metric("Glycaemic-excursion proxy","Not sampled")
    st.progress(item["wear"],text=f"Nightly temperature completeness {item['wear']:.0%}")

st.subheader("Illustrative what-if ranges")
st.caption("Illustrative assumptions, not a treatment recommendation. No intervention effect is clinically established.")
scenario=st.selectbox("Scenario",["Regular sleep","Daily walk","Lower-GI food swap","Lower evening stress","Illustrative weight change"])
factors={"Regular sleep":(.80,.98),"Daily walk":(.75,.98),"Lower-GI food swap":(.80,1.00),"Lower evening stress":(.80,1.00),"Illustrative weight change":(.75,.98)}
if st.button("Show illustrative range"):
    low,high=factors[scenario]
    st.write(f"Assumption-only range for E1 risk: {item['risk']*low:.0%}–{item['risk']*high:.0%}. This is not a treatment recommendation.")

st.subheader("Synthetic alert log")
predictions=[]
for r in rows:
    for day in (10,14,18):
        predictions.append({"patient":r["patient"],"cycle":r["cycle"],"day":day,
                            "risk":forecast(r["record"],day,2),"abstain":r["abstain"]})
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
st.caption("At most one alert per synthetic patient-cycle. Explanations are templated from state and feature contributions; no LLM is used in the loop.")
st.caption(DISCLAIMER)
