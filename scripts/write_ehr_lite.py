"""Write the synthetic, simulator-internal EHR-lite table used by tier 3."""
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.generator import generate


Path("data").mkdir(exist_ok=True)
seen = set()
with Path("data/ehr.csv").open("w", newline="", encoding="utf-8") as handle:
    fields = ["seed", "patient", "synthetic_archetype", "simulator_ir_latent", "simulator_androgen_load",
              "synthetic_age", "synthetic_bmi", "synthetic_family_history"]
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    for seed in (97, 101, 103):
        for row in generate(seed):
            key = (seed, row["patient"])
            if key in seen: continue
            seen.add(key)
            writer.writerow({"seed": seed, "patient": row["patient"], "synthetic_archetype": row["phenotype"],
                             "simulator_ir_latent": row["ir"], "simulator_androgen_load": row["androgen"],
                             "synthetic_age": row["age"], "synthetic_bmi": row["bmi"],
                             "synthetic_family_history": row["family_history"]})
print(f"Wrote {len(seen)} synthetic EHR-lite patient rows to data/ehr.csv")
