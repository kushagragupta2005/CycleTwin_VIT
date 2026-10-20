# Submission checklist

Source: [official challenge rules](https://api.unstop.com/hackathons/digital-twin-challenge-2026-happiest-health-1757873).

Status is evidence-based. A human-only action is not a completed submission. Recording is explicitly deferred by the user.

| Requirement | Status | Evidence / action |
|---|---|---|
| Public source repository | PASS | docs/public_access_check.json: anonymous HTTP checks |
| Team and college identified | PASS | README: solo participant Kushagra Gupta, Vellore Institute of Technology (VIT) |
| Project title | PASS | README title |
| Problem and healthcare use case | PASS | README; generated late/absent event, no diagnosis claim |
| Technical stack and model | PASS | README, requirements, model cards, src/inference.py |
| Synthetic or open data only | PASS | Repository generator and EHR-lite; published references are context, not training data |
| Static and dynamic stream fusion | PASS | src/features.py and persisted EHR-lite pipelines; oracle-adjacent disclosure |
| Working model and conceptual doctor UI | PASS | Persisted inference and Meet Kushi clinician view; covered by unit/AppTest checks |
| Open-source licence | PASS | MIT LICENSE and README |
| Architecture PDF | PASS | deliverables/CycleTwin_architecture.pdf; generated from claims and text-validated |
| Architecture PPTX | PASS | deliverables/CycleTwin_architecture.pptx; generated from claims and text-validated |
| Pitch Deck PDF | PASS | deliverables/CycleTwin_pitch_deck.pdf; generated from claims and text-validated |
| Pitch Deck PPTX | PASS | deliverables/CycleTwin_pitch_deck.pptx; generated from claims and text-validated |
| Required folder naming | PASS | Repository root CycleTwin_VIT; expected CycleTwin_VIT |
| README submission opening | PASS | Plain-language purpose, synthetic-data restriction, frozen snapshot, links, limitations, MIT licence and AI disclosure |
| Live-demo URL placeholder | HUMAN ACTION | Replace `LIVE_DEMO_URL` in README after a public deployment exists; do not invent a URL. |
| README link to minimum 20-minute video demonstration | HUMAN ACTION | Deferred by user. Human must record, upload, then supply the URL; do not invent one. |
| Full-time-student eligibility, team-size range and locked registered roster confirmed | HUMAN ACTION | Human leader must verify full-time eligibility, 1-4 members, confirmed details and no post-registration roster changes on Unstop. No registrar verification is available in this session. |
| Leader contact fields and final platform submission | HUMAN ACTION | Human leader enters their name, phone, email and public repository URL on Unstop before the deadline. Contact details are not published here. |

All technical checklist items pass only when their generated artifacts and tests remain current. CI and gate logs are linked from docs/gate_checks. Never claim clinical validity or use the persona as performance evidence.
