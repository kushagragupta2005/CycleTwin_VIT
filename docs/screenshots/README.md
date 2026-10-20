# Manual screenshot recapture

Status on 20 October 2026: the five existing PNG files predate the latest visual changes and have not been replaced. The automation browser inventory returned “Local browser use is disabled in Work settings.” These captures require the human operator.

Start the app from the repository folder with an activated environment:

    streamlit run app.py

Open http://localhost:8501 in Chrome. Keep the same window size for all five images, approximately 1440 × 1000 pixels at 100% browser zoom. Include the persistent research disclaimer and the sidebar settings where possible. Let each selection finish rendering; confirm the patient heading matches the selected ID before capturing.

Save directly over the following existing files in docs/screenshots/. The README already embeds these exact filenames.

| File to replace | Exact screen and actions | Required visible content |
|---|---|---|
| patient-list.png | Navigate → Cohort list. Display synthetic tier → Tier 2. Sort synthetic list → Risk. Scroll the main view to the top. | “Synthetic cohort” title, table headers, completeness bars, neutral and clinician-review badges, nearby benchmark context. |
| patient-timeline.png | Navigate → Patient view. Tier 2. Selected synthetic patient → s223-p0000. Scroll to the temperature trace. | Matching patient ID, cycle/ovulation estimate, temperature axes, interval band, period-start marker, missing-night markers and data-generated summary. |
| abstain-banner.png | Patient view. Tier 2. Select s223-p0026. Wait for the patient heading to change. | “Abstain · clinician review” banner, rule text “age or early post-menarche condition”, withheld risk state and conformal caption. |
| what-if-panel.png | Patient view. Tier 2. Select s223-p0000. Scroll to Illustrative what-if ranges. Choose Daily walk and click Show illustrative range. Open the What-if caveat. | Scenario selection, rendered assumption-only range and the full “not a treatment recommendation” caveat. |
| alert-log.png | Patient view. Select Tier 0 and patient s223-p0002. Scroll to Synthetic alert log and click Add selected synthetic alert to log once. | A populated log entry for s223-p0002, cycle 1 (zero-based stored index), the selected forecast day and score. Include the alert-log caveat; it states the one-alert budget and templated explanations. |

For the alert example, this patient's prior logged cycle length is 42 days and its Tier 0 fixed demo score is approximately 0.711. It is eligible at the dashboard's 0.50 cutoff. A second click should show the duplicate-protection message rather than add another entry.

Check all five files before submission: the same browser window size, correct patient/tier state, readable labels, visible disclaimers, and the latest page styling. Then commit only the five replaced PNGs and remove the “predate the latest visual changes” status from this guide and the main README.
