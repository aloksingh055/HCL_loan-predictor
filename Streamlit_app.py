"""
Main entry file for Streamlit Community Cloud.

One Streamlit process runs BOTH parts of the project:
  1. Backend  -> your existing FastAPI app (api.py), started in a background thread
  2. Frontend -> the dashboard pages inside the dashboard/ folder

The backend code is NOT changed or rewritten here. This file only loads
your existing api.py and serves it on 127.0.0.1 inside the same container,
so dashboard/api/client.py keeps calling it over HTTP exactly like before.

Place this file in the REPO ROOT and set it as the "Main file path" when deploying.
"""
import importlib.util
import os
import sys
import threading
import time
from pathlib import Path

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Paths and settings
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DASHBOARD_DIR = ROOT / "dashboard"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# >>> CHANGE THIS LIST if your api.py is somewhere else in the repo.
# The first path that exists is used.
BACKEND_FILE_CANDIDATES = [
    ROOT / "src" / "api.py",   # your layout: uvicorn src.api:app
    ROOT / "api.py",
    ROOT / "backend" / "api.py",
]

# Make the dashboard imports (api.client, utils.config, components.charts) work.
# DASHBOARD_DIR goes first so the dashboard's "api" package is found before any api.py.
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

# dashboard/utils/config.py reads API_BASE_URL from the environment.
# Streamlit Cloud has no .env file, so we set it here, before any dashboard import.
os.environ["API_BASE_URL"] = BACKEND_URL


# ---------------------------------------------------------------------------
# Backend launcher
# ---------------------------------------------------------------------------
def _backend_is_up() -> bool:
    try:
        return requests.get(f"{BACKEND_URL}/", timeout=1).ok
    except requests.RequestException:
        return False


def _find_backend_file() -> Path:
    for candidate in BACKEND_FILE_CANDIDATES:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(p.relative_to(ROOT)) for p in BACKEND_FILE_CANDIDATES)
    raise FileNotFoundError(
        f"api.py not found. Searched: {searched}. "
        "Edit BACKEND_FILE_CANDIDATES in streamlit_app.py."
    )


@st.cache_resource(show_spinner=False)
def start_backend() -> str:
    """Start the FastAPI backend once per server process (cached across reruns).

    NOTE: this function must not draw any Streamlit element, otherwise the
    st.set_page_config() calls inside the dashboard pages would fail.
    """
    # Local testing: if you already started uvicorn yourself, just reuse it.
    if _backend_is_up():
        return "already running"

    import uvicorn

    backend_file = _find_backend_file()

    # api.py looks for the model with relative paths (e.g. src/loan_model.pkl),
    # so load it while the working directory is the repo root.
    old_cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        # Loaded under a different module name so it does not clash with dashboard/api/.
        spec = importlib.util.spec_from_file_location("loan_backend", backend_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules["loan_backend"] = module
        spec.loader.exec_module(module)
    finally:
        os.chdir(old_cwd)

    if getattr(module, "model", None) is None:
        raise RuntimeError(
            "api.py loaded, but the model file was not found or could not be read. "
            "Make sure src/loan_model.pkl is committed to the repo "
            "(not blocked by .gitignore) and that scikit-learn/xgboost versions "
            "in requirements.txt match the ones used to train the model."
        )

    config = uvicorn.Config(module.app, host=BACKEND_HOST, port=BACKEND_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None  # signals only work in the main thread
    threading.Thread(target=server.run, daemon=True, name="loan-backend").start()

    for _ in range(60):  # wait up to ~30 seconds for the server to come up
        if _backend_is_up():
            return "started"
        time.sleep(0.5)
    raise RuntimeError("Backend did not become ready within 30 seconds.")


try:
    start_backend()
except Exception as exc:  # show a readable error instead of a crash
    st.set_page_config(page_title="Loan Risk Dashboard", layout="wide")
    st.error(f"Backend could not be started: {exc}")
    st.stop()


# ---------------------------------------------------------------------------
# Frontend: multipage navigation over the existing dashboard files
# ---------------------------------------------------------------------------
pages = [
    st.Page("dashboard/app.py", title="Home", icon="\U0001F3E0", default=True),
    st.Page("dashboard/pages/1_Single_Prediction.py", title="Single Prediction", icon="\U0001F9EE"),
    # Uncomment each page when you build it:
    # st.Page("dashboard/pages/2_Batch_Scoring.py", title="Batch Scoring"),
    # st.Page("dashboard/pages/3_Explainability_SHAP.py", title="Explainability (SHAP)"),
    # st.Page("dashboard/pages/4_Model_Performance.py", title="Model Performance"),
    # st.Page("dashboard/pages/5_Drift_Monitoring.py", title="Drift Monitoring"),
]

st.navigation(pages).run()