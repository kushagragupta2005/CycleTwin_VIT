"""Write SVG figures from result JSON; no hand-copied metric values."""
import html
import json
from pathlib import Path

data=json.loads(Path("docs/claims.json").read_text())["development"]
seeds=data["seeds"]
days=(10,14,18); tiers=(0,1,2,3)
colors={0:"#64748b",1:"#0f766e",2:"#d97706",3:"#9f5b86"}
Path("assets").mkdir(exist_ok=True)

def svg_start(title,subtitle,ymin,ymax,ylabel):
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="470" viewBox="0 0 900 470">',
           '<rect width="900" height="470" fill="#ffffff"/>',
           f'<text x="70" y="42" font-family="Arial" font-size="25" font-weight="700" fill="#172b3a">{html.escape(title)}</text>',
           f'<text x="70" y="68" font-family="Arial" font-size="14" fill="#596b76">{html.escape(subtitle)}</text>']
    x0,y0,x1,y1=90,105,830,390
    for i in range(6):
        val=ymin+(ymax-ymin)*i/5; y=y1-(val-ymin)/(ymax-ymin)*(y1-y0)
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#e2e8f0"/>')
        parts.append(f'<text x="55" y="{y+5:.1f}" font-family="Arial" font-size="13" fill="#596b76">{val:.2f}</text>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#596b76"/>')
    parts.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#596b76"/>')
    parts.append(f'<text x="20" y="245" transform="rotate(-90 20 245)" font-family="Arial" font-size="14" fill="#172b3a">{html.escape(ylabel)}</text>')
    for i,day in enumerate(days):
        x=x0+(x1-x0)*i/(len(days)-1)
        parts.append(f'<text x="{x-12:.1f}" y="{y1+25}" font-family="Arial" font-size="14" fill="#596b76">{day}</text>')
    parts.append(f'<text x="420" y="{y1+53}" font-family="Arial" font-size="14" fill="#172b3a">Forecast cycle day</text>')
    return parts,(x0,y0,x1,y1)

def render_auc():
    parts,box=svg_start("Synthetic development AUROC by tier","Mean across seeds 97, 101, 103; bars span the lowest to highest patient-cluster 95% interval",.3,1.0,"AUROC")
    x0,y0,x1,y1=box
    for tier in tiers:
        xs=[]; ys=[]
        for i,day in enumerate(days):
            rows=[s["metrics"][f"day_{day}_tier_{tier}"] for s in seeds.values()]
            mean=sum(r["auroc"] for r in rows)/len(rows)
            low=min(r["auroc_cluster_bootstrap_95ci"][0] for r in rows)
            high=max(r["auroc_cluster_bootstrap_95ci"][1] for r in rows)
            x=x0+(x1-x0)*i/(len(days)-1); y=y1-(mean-.3)/.7*(y1-y0)
            yl=y1-(low-.3)/.7*(y1-y0); yh=y1-(high-.3)/.7*(y1-y0)
            xs.append(x); ys.append(y)
            parts.append(f'<line x1="{x:.1f}" y1="{yh:.1f}" x2="{x:.1f}" y2="{yl:.1f}" stroke="{colors[tier]}" stroke-width="2"/>')
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{colors[tier]}"/>')
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in zip(xs,ys))}" fill="none" stroke="{colors[tier]}" stroke-width="3"/>')
        parts.append(f'<line x1="{570+tier*65}" y1="{115}" x2="{592+tier*65}" y2="{115}" stroke="{colors[tier]}" stroke-width="3"/><text x="{597+tier*65}" y="120" font-family="Arial" font-size="14" fill="#172b3a">Tier {tier}</text>')
    parts.append('</svg>')
    Path("assets/auroc_by_tier.svg").write_text("\n".join(parts))

def render_false_alerts():
    vals=[s["metrics"][f"day_{day}_tier_{tier}"]["false_alerts_per_100_cycles"] for s in seeds.values() for day in days for tier in tiers]
    ymax=max(5.0,((max(vals)//5)+1)*5)
    parts,box=svg_start("Synthetic development false alerts by tier","Mean false alerts per 100 patient-cycles at validation-selected thresholds; three generator seeds",0,ymax,"False alerts per 100 cycles")
    x0,y0,x1,y1=box
    for tier in tiers:
        xs=[]; ys=[]
        for i,day in enumerate(days):
            rows=[s["metrics"][f"day_{day}_tier_{tier}"] for s in seeds.values()]
            mean=sum(r["false_alerts_per_100_cycles"] for r in rows)/len(rows)
            x=x0+(x1-x0)*i/(len(days)-1); y=y1-mean/ymax*(y1-y0)
            xs.append(x); ys.append(y)
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{colors[tier]}"/>')
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in zip(xs,ys))}" fill="none" stroke="{colors[tier]}" stroke-width="3"/>')
        parts.append(f'<line x1="{570+tier*65}" y1="{115}" x2="{592+tier*65}" y2="{115}" stroke="{colors[tier]}" stroke-width="3"/><text x="{597+tier*65}" y="120" font-family="Arial" font-size="14" fill="#172b3a">Tier {tier}</text>')
    parts.append('</svg>')
    Path("assets/false_alerts_by_tier.svg").write_text("\n".join(parts))

render_auc(); render_false_alerts()

def render_tradeoff():
    parts,box=svg_start("Synthetic day-14 alert trade-off","Development mean across seeds; varying thresholds are descriptive only and were not used to choose the validation threshold",0,100,"False alerts per 100 cycles")
    x0,y0,x1,y1=box
    for tier in tiers:
        by_index=[]
        for seed in seeds.values():
            by_index.append(seed["metrics"][f"day_14_tier_{tier}"]["alert_tradeoff_curve"])
        points=[]
        for i in range(len(by_index[0])):
            false=sum(curve[i]["false_alerts_per_100_cycles"] for curve in by_index)/len(by_index)
            lead_values=[curve[i]["median_lead_days_vs_day_35"] for curve in by_index if curve[i]["median_lead_days_vs_day_35"] is not None]
            lead=sum(lead_values)/len(lead_values) if lead_values else 0
            x=x0+(x1-x0)*min(lead,35)/35; y=y1-false/100*(y1-y0); points.append((x,y))
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in points)}" fill="none" stroke="{colors[tier]}" stroke-width="3"/>')
        parts.append(f'<text x="{620+tier*50}" y="120" font-family="Arial" font-size="14" fill="{colors[tier]}">Tier {tier}</text>')
    parts.append(f'<text x="365" y="443" font-family="Arial" font-size="14" fill="#172b3a">Median lead days versus day 35</text>')
    parts.append('</svg>')
    Path("assets/lead_time_false_alarm_tradeoff.svg").write_text("\n".join(parts))

render_tradeoff()
