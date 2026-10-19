"""Templated explanations from state and model feature contributions."""

def explain_state(state: dict, contributions: dict[str,float], limit: int = 3) -> str:
    names={"temperature_shift":"nightly temperature pattern", "rhr_offset":"resting heart-rate pattern",
           "period_history":"logged cycle history", "shared_ir":"simulated insulin-resistance state"}
    ranked=sorted(contributions.items(),key=lambda item:abs(item[1]),reverse=True)[:limit]
    parts=[names.get(name,name.replace("_"," ")) for name,value in ranked if value != 0]
    ov=state.get("ovulation_estimate")
    if not parts: return "The demo has no strong feature contribution to summarize."
    summary="The synthetic forecast reflects "+", ".join(parts)+"."
    if ov is not None: summary+=f" The current ovulation-day estimate is {int(ov)}."
    return summary+" This is a model summary, not a clinical explanation."
