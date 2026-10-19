"""Explicit abstention rules for synthetic decision-support demonstrations."""

def abstention_reasons(record: dict, wear_threshold: float = 0.75) -> list[str]:
    reasons=[]
    if record.get("tsh_abnormal"): reasons.append("thyroid result outside simulated reference flag")
    if record.get("prolactin_abnormal"): reasons.append("prolactin result outside simulated reference flag")
    if record.get("hormonal_contraception"): reasons.append("hormonal contraception")
    if record.get("age", 99) < 18 or record.get("early_post_menarche"): reasons.append("age or early post-menarche condition")
    if record.get("pregnant") or record.get("postpartum") or record.get("breastfeeding"): reasons.append("pregnancy-related state")
    if record.get("perimenopausal"): reasons.append("perimenopausal age band")
    if record.get("wear_completeness", 1.0) < wear_threshold: reasons.append("wear-time completeness below threshold")
    return reasons

def abstain(record: dict, wear_threshold: float = 0.75) -> bool:
    return bool(abstention_reasons(record, wear_threshold))
