.PHONY: all demo-apple test
all:
	python3 scripts/run_eval.py
	python3 scripts/update_readme_results.py
	python3 scripts/generate_figures.py

demo-apple:
	python3 scripts/make_synthetic_apple_export.py
	streamlit run app.py

test:
	python3 -m unittest discover -s tests
