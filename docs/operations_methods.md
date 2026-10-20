# Local operations measurement

`scripts/measure_ops.py` validates and loads one persisted frozen Tier-2 model, then measures 1,000 in-process predictions for a generated cycle. It separately measures one new Python subprocess from launch through its first prediction. RSS is local-process `ru_maxrss`, not container memory or a production-service measurement. Hardware, Python build and system load affect these figures; they are evidence for this run only.
