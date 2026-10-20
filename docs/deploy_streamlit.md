# Deploy on Streamlit Community Cloud

The main file is `app.py`, which loads the reviewed v3 interface. The preserved
pre-v3 dashboard is available locally as `app_legacy.py`. Dependencies are pinned
in `requirements.txt`.

1. Push the repository to GitHub.
2. In Streamlit Community Cloud, create an app from the repository and select `app.py` as the main file.
3. Select Python 3.11 if the version selector is offered, to match CI.
4. Deploy, then open the app once before judging.

Initial load may take time on a free tier; open it once before judging.

The app reads repository-relative tracked assets and uses the operating system temporary directory for uploaded Apple Health XML handling. It does not require a writable repository directory or a machine-specific path.
