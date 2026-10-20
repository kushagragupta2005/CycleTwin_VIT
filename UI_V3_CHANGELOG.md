# UI v3 changelog

## Stage 1 — design system and Home page

- Added the isolated entry point `app_v3.py` and the `ui3/` design-system files.
- Left `app.py`, model code, data, persisted artifacts, evaluation logic, and `.streamlit/config.toml` unchanged.
- The Home metrics are read from `docs/claims.json` through `src.claims.load_claims`; no metric values are entered in UI code.
- The existing navigation session key is `view`; the mock-consent control now has the explicit `mock_consent` key in the isolated v3 app.

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
