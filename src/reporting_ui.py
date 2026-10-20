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
    st.caption('In plain words: each cycle can alert once, at the earliest safe threshold crossing on day 10, 14 or 18. These are simulator outcomes, not clinical alert rates.')
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


def render_bayesian_twin(claims):
    result=claims.get('bayesian_twin')
    if not result: return
    means=result['mean_across_seeds'];ci=result['pooled_patient_cluster_95ci']
    st.subheader('Frozen synthetic timing-posterior check')
    st.caption('In plain words: a train-only calendar/static prior plus temperature, RHR and HRV likelihoods estimates a distribution over generated ovulation days or absence.')
    st.dataframe(pd.DataFrame([{'Twin Brier':means['twin_brier'],'Logistic Brier':means['logistic_brier'],
                                'Twin minus logistic Brier':means['twin_minus_logistic_brier'],'Patient-cluster 95% CI':ci,
                                'Status':result['status']}]),hide_index=True,use_container_width=True)
    st.caption('This synthetic timing posterior is reported separately. It does not replace the fitted logistic score, threshold, safety gate or alert policy.')


def render_lab_proxy(claims):
    result=claims.get('lab_proxy')
    if not result: return
    st.subheader('Simulated assay-like extension')
    st.caption('In plain words: noisy positive simulator indices were added to Tier 2. They are not hormone measurements and are kept separate from the frozen primary endpoint.')
    means=result['means'];upper=result['original_tier3_upper_bound_means']
    st.dataframe(pd.DataFrame([{'Post-freeze synthetic lab-like AUROC':means['auroc'],'Standard AP':means['average_precision'],'Brier':means['brier'],
                                'Original Tier-3 internal-reference AUROC':upper['auroc'],'Original Tier-3 internal-reference Brier':upper['brier']}]),hide_index=True,use_container_width=True)
    st.caption('The indices derive from label-generating simulator latents, with 15% assay noise. They have no clinical units and retain simulator-internal leakage risk.')


def render_operations(claims):
    ops=claims.get('operations')
    if not ops: return
    st.subheader('Local operations measurement')
    st.caption('In plain words: this is a local machine timing check for one persisted synthetic model, not a production service guarantee.')
    warm=ops['warm_latency_ms']
    st.dataframe(pd.DataFrame([{'Cold subprocess (ms)':ops['cold_subprocess_ms'],'Warm mean (ms)':warm['mean'],'Warm p95 (ms)':warm['p95'],
                                'Warm repeats':ops['warm_repeats'],'Process peak RSS (KiB)':ops['process_peak_rss_kib']}]),hide_index=True,use_container_width=True)
    st.caption(ops['rss_note'])


def render_conformal(claims):
    summary=claims.get('conformal_summary')
    if not summary: return
    st.subheader('Frozen synthetic conformal coverage')
    st.caption('In plain words: the classification set covers the generated event label at about its 90% target. The separate heuristic day band does not achieve useful frozen coverage.')
    st.dataframe(pd.DataFrame([{'Day-18 Tier-2 classification coverage':summary['classification_coverage_mean'],
                                'Mean classification-set size':summary['mean_classification_set_size'],
                                'Heuristic day-band coverage':summary['day_band_coverage_mean'],
                                'Day-band mean width (days)':summary['day_band_mean_width']}]),hide_index=True,use_container_width=True)
    st.caption('Coverage is marginal, synthetic and generator-specific. The day band remains an illustration and is not a reliable timing interval.')
