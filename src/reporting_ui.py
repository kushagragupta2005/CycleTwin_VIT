"""Read-only diagnostic tables from generated claims."""
from pathlib import Path
import pandas as pd
import streamlit as st


def render_reporting(claims, default_tier=2):
    report=claims.get('reporting')
    if not report:
        st.info('Additional synthetic reporting is pending.');return
    st.subheader('Synthetic calibration and subgroup diagnostics')
    st.caption('In plain words: inspect where probability errors and missed generated events differ across groups. These diagnostic fits never change the predictor or threshold.')
    days=claims['configuration']['days'];tiers=claims['configuration']['tiers']
    controls=st.columns(3)
    with controls[0]: day=st.selectbox('Diagnostic snapshot',days,index=len(days)-1,key='reporting_day')
    with controls[1]: tier=st.selectbox('Diagnostic tier',tiers,index=tiers.index(default_tier),key='reporting_tier')
    groups=next(iter(report['frozen'].values()))[f'day_{day}_tier_{tier}']
    with controls[2]: subset=st.selectbox('Diagnostic subset',list(groups),key='reporting_subset')
    rows=[]
    for seed,sr in report['frozen'].items():
        m=sr[f'day_{day}_tier_{tier}'][subset]
        if not m['n']: continue
        diagnostic=m['calibration_diagnostic']
        rows.append({'Frozen synthetic seed':seed,'Cycles':m['n'],'People':m['patients'],
                     'Positive/negative':f"{m['positive']}/{m['negative']}",
                     'AUROC':m['auroc'],'AUROC patient CI':m['intervals']['auroc']['95ci'],
                     'Standard AP':m['average_precision'],'Recall':m['recall'],
                     'Recall patient CI':m['intervals']['recall']['95ci'],'ECE':m['ece'],
                     'Diagnostic intercept':diagnostic['intercept'],'Diagnostic slope':diagnostic['slope']})
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.caption('ECE uses the predeclared equal-width score bins and depends on binning. Sparse subgroups have wide or undefined intervals. Calibration slope/intercept are held-out reporting diagnostics, not a newly deployed calibration.')
    for name,caption in [('reliability.svg','Frozen synthetic Tier-2 reliability by snapshot; counts pooled across the separate seed models.'),
                         ('decision_curve.svg','Frozen synthetic day-18 decision curves. Threshold odds are assumptions; this does not establish clinical utility.')]:
        path=Path('docs/figures')/name
        if path.exists(): st.image(str(path),caption=caption)


def render_alert_policy(claims):
    summary=claims.get('alert_policy_summary')
    if not summary: return
    st.subheader('Frozen synthetic sequential alert policy')
    st.caption('In plain words: each cycle can alert once, at the first safe threshold crossing on day 10, 14 or 18. These are simulator outcomes, not clinical alert rates.')
    rows=[]
    for tier,metrics in summary.items():
        rows.append({'Tier':int(tier),'Synthetic cycles':metrics['n_cycles'],'Alerts':metrics['alerts'],
                     'Alert precision':metrics['alert_precision'],'Missed generated events':metrics['missed_events'],
                     'Missed-event rate':metrics['missed_event_rate'],
                     'False alerts / synthetic patient-year':metrics['false_alerts_per_synthetic_patient_year'],
                     'Median lead time (days)':metrics['lead_time_days_median'],'Lead-time n':metrics['lead_time_n']})
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.caption('Lead time is generated ovulation day minus alert day for true-positive cycles with a generated ovulation day. Absent ovulation has no numerical lead time. Safety is evaluated at each snapshot; later information cannot change an earlier alert.')


def render_robustness(claims):
    report=claims.get('robustness')
    if not report: return
    st.subheader('Frozen synthetic robustness extension')
    st.caption('In plain words: the saved day-18 Tier-2 models see perturbed synthetic inputs. Model weights and thresholds remain fixed.')
    path=Path('docs/figures/robustness.svg')
    if path.exists(): st.image(str(path),caption='AUROC and Brier across the predeclared synthetic sweeps. Safety-withhold rate is in the generated JSON and CSV.')
    st.caption('Added missing readings, added noise, bias, drift and generated timing shifts are sensitivity tests. They do not validate any real device or clinical workflow.')
