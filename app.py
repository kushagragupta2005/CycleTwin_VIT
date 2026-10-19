import streamlit as st
from src.adapters.apple_health import parse_export

st.set_page_config(page_title="CycleTwin | synthetic demo", layout="wide")
st.title("CycleTwin — synthetic cycle forecast demo")
st.caption("Synthetic demo data only. Not for diagnosis, contraception or conception planning.")
st.info("This interface illustrates a data path. It does not produce validated clinical forecasts.")
demo_path="apple_health_export/export.xml"
if __import__("os").path.exists(demo_path):
    parsed=parse_export(demo_path)
    st.subheader("Synthetic Apple Health export")
    st.metric("Dates parsed",len(parsed["daily"]))
    st.write("Cycle starts",parsed["cycle_starts"])
    st.dataframe([{"date":d,**v} for d,v in sorted(parsed["daily"].items())],use_container_width=True)
uploaded = st.file_uploader("Load a synthetic Apple Health export XML", type=["xml"])
if uploaded:
    path="/tmp/cycletwin_uploaded_export.xml"
    with open(path,"wb") as f: f.write(uploaded.getvalue())
    parsed=parse_export(path)
    st.metric("Synthetic dates",len(parsed["daily"]))
    st.write("Cycle starts",parsed["cycle_starts"])
    st.dataframe([{"date":d,**v} for d,v in sorted(parsed["daily"].items())],use_container_width=True)
st.caption("Sensor tier: synthetic XML subset · Data completeness: parser coverage only · Mock consent: synthetic data")
