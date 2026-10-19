"""Deterministic patient-level held-out split used by the synthetic benchmark."""

def patient_partition(patient_id: str) -> str:
    idx = int(patient_id.split("p")[-1])
    bucket = idx % 20
    return "test" if bucket < 3 else "validation" if bucket < 6 else "train"
