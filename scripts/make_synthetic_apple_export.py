from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree
from src.generator import generate

root = Element("HealthData", {"locale":"en_US"})
patient = generate(17, patients=1, cycles=1)[0]
start = str(patient["period_start"])
for day in range(35):
    date = str(patient["period_start"] + __import__("numpy").timedelta64(day, "D"))
    records = [
        ("HKQuantityTypeIdentifierAppleSleepingWristTemperature", "degC", 36.4 + float(patient["temperature"][day])),
        ("HKQuantityTypeIdentifierRestingHeartRate", "count/min", 62 + float(patient["rhr"][day])),
        ("HKQuantityTypeIdentifierHeartRateVariabilitySDNN", "ms", 48 + float(patient["hrv"][day])*4),
        ("HKQuantityTypeIdentifierStepCount", "count", float(patient["steps"][day])),
    ]
    for typ, unit, value in records:
        SubElement(root, "Record", {"type":typ, "unit":unit, "value":f"{value:.3f}",
            "startDate":date+" 23:00:00 +0530", "endDate":date+" 23:59:00 +0530"})
    sleep_start=datetime.strptime(date+" 22:30:00 +0530","%Y-%m-%d %H:%M:%S %z")
    for stage,hours in (("Core",3.4),("Deep",1.1),("REM",1.5),("Awake",.4)):
        sleep_end=sleep_start+timedelta(hours=hours)
        SubElement(root,"Record",{"type":"HKCategoryTypeIdentifierSleepAnalysis",
            "value":"HKCategoryValueSleepAnalysis"+("Awake" if stage=="Awake" else "Asleep"+stage),
            "startDate":sleep_start.strftime("%Y-%m-%d %H:%M:%S %z"),
            "endDate":sleep_end.strftime("%Y-%m-%d %H:%M:%S %z")})
        sleep_start=sleep_end
    if day == 0:
        rec = SubElement(root, "Record", {"type":"HKCategoryTypeIdentifierMenstrualFlow", "value":"2",
            "startDate":date+" 08:00:00 +0530", "endDate":date+" 08:01:00 +0530"})
        SubElement(rec, "MetadataEntry", {"key":"HKMetadataKeyMenstrualCycleStart", "value":"true"})
Path("apple_health_export").mkdir(exist_ok=True)
ElementTree(root).write("apple_health_export/export.xml", encoding="utf-8", xml_declaration=True)
from src.adapters.apple_health import parse_export
parsed = parse_export("apple_health_export/export.xml")
print(f"Synthetic export parsed: {len(parsed['daily'])} dates, cycle starts={parsed['cycle_starts']}")

