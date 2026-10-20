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
