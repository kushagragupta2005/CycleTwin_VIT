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
