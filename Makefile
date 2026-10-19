.PHONY: all demo-apple test
all:
	python3 scripts/run_eval.py

demo-apple:
	python3 scripts/make_synthetic_apple_export.py
	streamlit run app.py

test:
	python3 -m unittest discover -s tests
