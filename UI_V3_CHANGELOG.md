# UI v3 changelog

## Stage 1 — design system and Home page

- Added the isolated entry point `app_v3.py` and the `ui3/` design-system files.
- Left `app.py`, model code, data, persisted artifacts, evaluation logic, and `.streamlit/config.toml` unchanged.
- The Home metrics are read from `docs/claims.json` through `src.claims.load_claims`; no metric values are entered in UI code.
- The existing navigation session key is `view`; the mock-consent control now has the explicit `mock_consent` key in the isolated v3 app.

## Stage 2 — synthetic patients and Home action spacing

- Corrected spacing between the Home action buttons and between the Kushi scenario card and its action, including the narrow layout.
- Added the `Synthetic patients` view: a tier selector, sorting control, readable status legend, synthetic-data label, and a patient table that changes into labeled rows on narrow screens.
- Each row uses an icon and text for its status: not flagged, flagged for review, or score withheld. The tier-specific scores and withheld states are generated through the existing inference and safety paths.
- Preserved the selected generated patient in the existing session state so the following patient-view stage can open it. No model, data, score, threshold, or safety-rule logic changed.

## Stage 3 — individual generated-record view

- Added `One patient`, which uses the selected generated record and the existing persisted Tier model, explicit safety gate, uncertainty helper, twin simulator, CGM illustration, sandbox, and one-alert policy.
- Preserved the withheld-score path: it shows the fired rule and observed temperature trace while withholding the score, interval, feature evidence, sandbox, and alerts.
- Made the failed synthetic ovulation-day band visible beside the temperature trace, including its inability to meet its 90% coverage target.
- Added data-derived chart summaries, an optional fitted-feature table, and narrow-screen layout verification. No model, data, score, threshold, safety-rule, or simulator logic changed.

## Stage 4 — clearer findings and Evidence page

- Rewrote the four Home findings in judge-facing language while continuing to read AUROC, coverage, target, tier, day, sample count, and seed count from `docs/claims.json`.
- Made the timing-range failure explicit with a warning icon, `Failed` label, and red card. Detailed mode reveals the associated technical metric and tier/day under every finding.
- Added `Evidence`: frozen tier results, synthetic uncertainty and one-alert-policy checks, optional diagnostics, local operations details, and visible research limitations.

## Stage 5 — Meet Kushi fictional scenario

- Added an isolated, explicitly fictional Kushi page with the declared no-score selection rule, generated history, selectable scenarios, sensor tiers, and forecast snapshots.
- Kept static simulator internals inside an advanced disclosure, labelled oracle-adjacent and separate from hormone measurements or real EHR data.
- Added live fictional guardrails that reuse the existing fail-closed safety path; a hormonal-contraception check was verified to withhold the score.

## Stage 6 — About and safety

- Added the final v3 page: scope boundaries, explicit fail-closed score-withholding rules, session-level mock-consent status, and judge-facing glossary.
- Moved the unchanged synthetic Apple Health-shaped XML loader and upload parser into Advanced tools. The bundled synthetic export was generated and parsed locally: 36 dates and one cycle start; it remains outside the scored cohort.
- Added the shared not-for-diagnosis footer to every non-Home v3 view.

## Stage 7 — guided tour

- Connected Home’s 60-second tour to the existing three generated walkthrough records: the normal Tier-2 view, the Tier-2 withheld-score view, and the Tier-0 alert-policy view.
- Added Back, Next, and Finish controls that retain the selected record and tier through the established session state. All three steps were verified in the running preview.

## Run and rollback

```sh
# Preview v3
streamlit run app_v3.py

# Return to the unchanged current application
streamlit run app.py

# Discard the isolated redesign branch
git switch main
git branch -D ui/v3-redesign
```
