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
