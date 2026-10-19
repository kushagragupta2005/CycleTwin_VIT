"""Streaming parser for a limited Apple Health export.xml subset."""
from datetime import datetime
from xml.etree.ElementTree import iterparse
import csv

QUANTITY = {
    "HKQuantityTypeIdentifierAppleSleepingWristTemperature": "temperature",
    "HKQuantityTypeIdentifierRestingHeartRate": "rhr",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "hrv",
    "HKQuantityTypeIdentifierStepCount": "steps",
}
def parse_export(path):
    daily, starts = {}, []
    for _, el in iterparse(path, events=("end",)):
        if el.tag == "Record":
            typ = el.attrib.get("type", "")
            date = el.attrib.get("startDate", "")[:10]
            if typ in QUANTITY and date:
                key = QUANTITY[typ]
                unit = el.attrib.get("unit", "")
                val = float(el.attrib.get("value", 0))
                if key == "temperature" and unit in ("degF", "°F"):
                    val = (val - 32) * 5 / 9
                daily.setdefault(date, {})[key] = val
            elif typ == "HKCategoryTypeIdentifierMenstrualFlow":
                meta = {x.attrib.get("key"): x.attrib.get("value") for x in el.findall("MetadataEntry")}
                if meta.get("HKMetadataKeyMenstrualCycleStart", "false").lower() == "true":
                    starts.append(date)
            elif typ == "HKCategoryTypeIdentifierSleepAnalysis" and date:
                stage=el.attrib.get("value","")
                stage_map={"HKCategoryValueSleepAnalysisAsleepCore":"core",
                           "HKCategoryValueSleepAnalysisAsleepDeep":"deep",
                           "HKCategoryValueSleepAnalysisAsleepREM":"rem",
                           "HKCategoryValueSleepAnalysisAwake":"awake",
                           "HKCategoryValueSleepAnalysisAsleep":"asleep"}
                key=stage_map.get(stage)
                if key:
                    start=datetime.strptime(el.attrib["startDate"],"%Y-%m-%d %H:%M:%S %z")
                    end=datetime.strptime(el.attrib["endDate"],"%Y-%m-%d %H:%M:%S %z")
                    daily.setdefault(date,{})[f"sleep_{key}_hours"] = daily.setdefault(date,{}).get(f"sleep_{key}_hours",0.0)+(end-start).total_seconds()/3600
            el.clear()
        elif el.tag == "Workout":
            el.clear()
    return {"daily": daily, "cycle_starts": sorted(set(starts))}

def read_generic_csv(path):
    """Read date,temp,rhr,hrv,steps,period_start CSV from other platforms."""
    daily, starts = {}, []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            date = row.get("date", "")
            if not date: continue
            daily[date] = {k: (float(row[k]) if row.get(k) else None)
                           for k in ("temp", "rhr", "hrv", "steps")}
            if row.get("period_start", "").lower() in ("1", "true", "yes"):
                starts.append(date)
    return {"daily": daily, "cycle_starts": starts}

