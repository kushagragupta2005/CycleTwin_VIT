"""Patient-cycle alert budget with an explicit abstention guard."""

def apply_alert_budget(predictions, threshold: float = 0.50, max_per_cycle: int = 1):
    grouped={}
    for row in predictions:
        key=(row["patient"],row["cycle"])
        grouped.setdefault(key,[]).append(row)
    output=[]
    for key,rows in grouped.items():
        eligible=[r for r in rows if r.get("abstain") is False and r["risk"] >= r.get("threshold", threshold)]
        selected=sorted(eligible,key=lambda r:r["risk"],reverse=True)[:max_per_cycle]
        selected_ids={id(r) for r in selected}
        for row in rows:
            out=dict(row); out["alert"]=id(row) in selected_ids; output.append(out)
    return output


def apply_sequential_alert_policy(predictions, max_per_cycle: int = 1):
    """Commit the earliest eligible snapshot decision for each patient-cycle.

    Rows must contain a day, score, threshold and explicit abstention result.
    Later rows are never allowed to replace an earlier selected alert.
    """
    grouped = {}
    for row in predictions:
        grouped.setdefault((row["patient"], row["cycle"]), []).append(row)
    output = []
    for rows in grouped.values():
        ordered = sorted(rows, key=lambda r: r["day"])
        selected = []
        for row in ordered:
            eligible = row.get("abstain") is False and row["risk"] >= row["threshold"]
            if eligible and len(selected) < max_per_cycle:
                selected.append(id(row))
        for row in ordered:
            out = dict(row)
            out["alert"] = id(row) in selected
            output.append(out)
    return output
