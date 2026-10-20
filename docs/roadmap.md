# Roadmap

| Work item | Status | Current boundary |
|---|---|---|
| Structured clinician review | **Not done** | Use [clinician_review_kit.md](clinician_review_kit.md) before changing clinical-facing language. |
| mcPHASES access | **Not done** | PhysioNet credentialing is restricted and has not been obtained; no records are used. |
| Pre-ovulatory signal branch | **Not done** | Urinary LH and cervical-mucus inputs require consented data and a prospective design. |
| Sim-to-real evaluation | **Not done** | Synthetic labels and signals share generator assumptions. |

## Real-data gap

| Synthetic component | Real-data requirement | Status |
|---|---|---|
| Generated event label | Prospectively defined and independently confirmed endpoint | **Not done** |
| Wearable-style temperature | Device-specific quality checks and missingness study | **Not done** |
| Oracle-adjacent EHR-lite | Clinically collected features without label-generating internals | **Not done** |
| Safety rules | Clinician review and prospective safety evaluation | **Not done** |
