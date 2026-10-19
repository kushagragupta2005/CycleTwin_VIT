.PHONY: all demo-apple
all:
	python scripts/run_eval.py

demo-apple:
	python scripts/make_synthetic_apple_export.py
	streamlit run app.py
