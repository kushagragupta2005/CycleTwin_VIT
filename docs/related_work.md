# Related work

The cited work provides context for the design and reporting choices. It does not validate CycleTwin.

- Goodale et al. studied wearable physiology across menstrual phases and fertile-window prediction: *J Med Internet Res* 2019;21(4):e13404. https://doi.org/10.2196/13404
- Luo et al. studied ovulation detection and prediction from high-frequency in-ear temperature: *IEEE Trans Biomed Eng* 2020;67(2):512–522. https://doi.org/10.1109/TBME.2019.2916823
- Wang et al. evaluated wrist-temperature algorithms for retrospective ovulation-day estimation and next-menses prediction: *Hum Reprod* 2025;40(3):469–478. https://doi.org/10.1093/humrep/deaf005
- Awoniran, Lawlor, Gaunt and Millard reported a vaginal-temperature machine-learning study for PMOS identification. This is a medRxiv preprint and is not peer reviewed: https://doi.org/10.64898/2026.07.23.26358666
- Shamanna et al. reported a single-patient digital-twin case study: *AACE Clin Case Rep* 2025;11(1):70–74. https://doi.org/10.1016/j.aace.2024.11.004
- Lin et al. examined continuous glucose measurements across menstrual-cycle phases: *npj Digit Med* 2023;6:140. https://doi.org/10.1038/s41746-023-00884-x
- Teede et al. published the 2023 International Evidence-based Guideline: *J Clin Endocrinol Metab* 2023;108(10):2447–2469. https://doi.org/10.1210/clinem/dgad463
- Teede et al. described the 2026 consensus name polyendocrine metabolic ovarian syndrome (PMOS), previously PCOS: *The Lancet* 2026. https://doi.org/10.1016/S0140-6736(26)00717-8
- Gibbs and Candès introduced adaptive conformal inference under distribution shift at NeurIPS 2021: https://papers.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html
- Collins et al. published TRIPOD+AI reporting guidance: *BMJ* 2024;385:e078378. https://doi.org/10.1136/bmj-2023-078378
- mcPHASES is listed as a restricted-access menstrual-health dataset on PhysioNet. It is a roadmap item only; no records are used or bundled: https://physionet.org/content/mcphases/1.0.0/

CycleTwin's G1 benchmark forecasts a synthetic current-cycle event using a fixed score and a temperature coverline heuristic. The dashboard also contains a simplified coupled simulator, which is not used by that benchmark and is not clinically calibrated. The wearable studies above concern real cohort data or different prediction targets; the single-patient report is a case study; the vaginal-temperature work is a preprint. No cross-study performance comparison is made.

Apple HealthKit type identifiers are documented separately in the adapter source and in Apple's developer documentation: https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/applesleepingwristtemperature and https://developer.apple.com/documentation/healthkit/hkcategorytypeidentifier/menstrualflow.
