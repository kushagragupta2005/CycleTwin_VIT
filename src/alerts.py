"""Patient-cycle alert budget with an explicit abstention guard."""

def apply_alert_budget(predictions, threshold: float = 0.50, max_per_cycle: int = 1):
    grouped={}
    for row in predictions:
        key=(row["patient"],row["cycle"])
        grouped.setdefault(key,[]).append(row)
    output=[]
    for key,rows in grouped.items():
        eligible=[r for r in rows if not r.get("abstain",False) and r["risk"] >= r.get("threshold", threshold)]
        selected=sorted(eligible,key=lambda r:r["risk"],reverse=True)[:max_per_cycle]
        selected_ids={id(r) for r in selected}
        for row in rows:
            out=dict(row); out["alert"]=id(row) in selected_ids; output.append(out)
    return output
