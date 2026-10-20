"""Explicit fail-closed safety rules for synthetic decision-support demonstrations."""
import math

BOOLEAN_FIELDS = ("tsh_abnormal", "prolactin_abnormal", "hormonal_contraception",
                  "early_post_menarche", "pregnant", "postpartum", "breastfeeding", "perimenopausal")

def abstention_reasons(record: dict, wear_threshold: float = 0.75) -> list[str]:
    reasons=[]
    missing = [name for name in BOOLEAN_FIELDS if type(record.get(name)) is not bool]
    for name in ("age", "wear_completeness"):
        value = record.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            missing.append(name)
    if missing:
        reasons.append("missing or invalid safety information: " + ", ".join(missing))
    if record.get("tsh_abnormal"): reasons.append("thyroid result outside simulated reference flag")
    if record.get("prolactin_abnormal"): reasons.append("prolactin result outside simulated reference flag")
    if record.get("hormonal_contraception"): reasons.append("hormonal contraception")
    if ("age" not in missing and record["age"] < 18) or record.get("early_post_menarche") is True: reasons.append("age or early post-menarche condition")
    if record.get("pregnant") or record.get("postpartum") or record.get("breastfeeding"): reasons.append("pregnancy-related state")
    if record.get("perimenopausal"): reasons.append("perimenopausal age band")
    if "wear_completeness" not in missing:
        wear=record["wear_completeness"]
        if not 0 <= wear <= 1: reasons.append("invalid wear-time completeness")
        elif wear < wear_threshold: reasons.append("wear-time completeness below threshold")
    return reasons

def abstain(record: dict, wear_threshold: float = 0.75) -> bool:
    return bool(abstention_reasons(record, wear_threshold))


def synthetic_safety_record(record, day):
    """Explicit known simulator flags; never infer a normal clinical lab from missing data."""
    import numpy as np
    phenotype = record.get("phenotype")
    flags = {name: False for name in BOOLEAN_FIELDS} if phenotype else {}
    flags.update(age=record.get("age"))
    if phenotype:
        flags.update(tsh_abnormal=phenotype == "thyroid_mimic",
                     hormonal_contraception=phenotype == "contraception",
                     early_post_menarche=phenotype == "early_menarche")
    values = np.asarray(record.get("temperature", []), dtype=float)[:day]
    flags["wear_completeness"] = float(np.isfinite(values).sum() / day) if day > 0 else None
    return flags
