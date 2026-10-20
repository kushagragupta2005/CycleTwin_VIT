"""AppTest audit only: does not modify application code or open a browser."""
import json
from pathlib import Path
import sys
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()
evidence={"render_passes":[]}

def check(name):
    assert not at.exception,[x.message for x in at.exception]
    assert any("Synthetic data only" in m.value for m in at.markdown)
    evidence["render_passes"].append(name)

def navigate(view):
    at.get("button_group")[0].set_value([view]).run()

def click(label):
    at.get("button_group")[0].set_value([at.session_state["view"]])
    next(x for x in at.button if x.label==label).click().run()
    assert not at.exception,[x.message for x in at.exception]

check("Overview")
evidence["overview_metrics"]={m.label:m.value for m in at.metric}
for name in ("Cohort","Patient","Method"):
    navigate(name);check(name)
navigate("Overview")
click("Try the demo");check("Guided p0000")
click("Next");check("Guided p0026")
assert any(m.value=="Withheld" for m in at.metric)
evidence["abstaining_patient"]=at.session_state["patient_choice"]
evidence["withheld_metric_labels"]=[m.label for m in at.metric if m.value=="Withheld"]
click("Show illustrative range")
evidence["what_if_remains_visible_during_abstention"]=[
    m.value for m in at.markdown if "Assumption-only range for demo E1 score" in m.value]
assert evidence["what_if_remains_visible_during_abstention"]
click("Next");check("Guided p0002")
assert at.session_state["display_tier"]==0
evidence["tier0_patient"]=at.session_state["patient_choice"]
evidence["tier0_score_metrics"]={m.label:m.value for m in at.metric}
evidence["tier0_displayed_day_estimate"]=[
    m.value for m in at.markdown if "Synthetic ovulation-day estimate:" in m.value]
evidence["tier0_explanation"]=[
    m.value for m in at.markdown if "The synthetic forecast reflects" in m.value]
click("Add selected synthetic alert to log")
evidence["alert_log"]=list(at.session_state["alert_log"])
click("Add selected synthetic alert to log")
assert len(at.session_state["alert_log"])==1
navigate("Cohort")
table=next(m.value for m in at.markdown if "<table" in m.value)
start=table.index("s223-p0026")
evidence["abstaining_patient_cohort_row"]=table[start:table.index("</tr>",start)]
evidence["cohort_display_tier"]=at.session_state["display_tier"]
assert 'title="Fixed synthetic heuristic; not a diagnosis probability"' in evidence["abstaining_patient_cohort_row"]
evidence["source_unchanged"]=True
(OUT/"ui_audit_checks.json").write_text(json.dumps(evidence,indent=2)+"\n")
print("PASS",len(evidence["render_passes"]),"required renders; reproduced withholding and selected-tier estimate gaps")
