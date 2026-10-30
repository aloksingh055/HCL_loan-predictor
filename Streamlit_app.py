"""
Main entry file for Streamlit Community Cloud (Streamlit_app.py).

One Streamlit process runs BOTH parts of the project:
  1. Backend  -> your existing FastAPI app (src/api.py), started in a background thread
  2. Frontend -> the dashboard pages inside dashboard/pages/

Repo layout this file expects (this file lives in the REPO ROOT):

    loan-default-predictor/                 <- repo root
    |-- Streamlit_app.py                    <- this file (the "Main file path" on Streamlit Cloud)
    |-- requirements.txt                    <- needed for deployment (put it here, in the repo root)
    |-- loan-risk-predictor/                <- app folder (found automatically)
    |   |-- src/
    |   |   |-- api.py                      <- FastAPI backend (app = FastAPI(...))
    |   |   `-- loan_model.pkl              <- trained model, loaded by api.py
    |   `-- dashboard/
    |       |-- app.py                      <- Home page
    |       |-- pages/                      <- 1_Single_Prediction.py, 2_Batch_Scoring.py, ...
    |       |-- api/client.py               <- all backend calls (HTTP to 127.0.0.1:8000)
    |       `-- components/, utils/
    |-- venv/, Postgresql/                  <- local only (ignored by Git)

If you ever move dashboard/ and src/ next to this file, it still works: the app
folder is detected automatically.

The backend code is NOT changed or rewritten here. This file only loads your
existing src/api.py and serves it on 127.0.0.1 inside the same container, so
dashboard/api/client.py keeps calling it over HTTP exactly like before.
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
ROOT = Path(__file__).resolve().parent  # repo root (where this file is)

# App folder = the folder that contains dashboard/app.py and src/api.py.
# Checked in this order: loan-risk-predictor/ first, then the repo root itself.
APP_DIR = next(
    (p for p in (ROOT / "loan-risk-predictor", ROOT) if (p / "dashboard" / "app.py").exists()),
    None,
)
if APP_DIR is None:
    st.set_page_config(page_title="Loan Risk Dashboard", layout="wide")
    st.error(
        "dashboard/app.py was not found. Expected it in loan-risk-predictor/dashboard/ "
        "(or dashboard/ next to Streamlit_app.py)."
    )
    st.stop()

DASHBOARD_DIR = APP_DIR / "dashboard"
PAGES_DIR = DASHBOARD_DIR / "pages"

# >>> CHANGE THIS if your backend file moves (local command: uvicorn src.api:app)
BACKEND_FILE = APP_DIR / "src" / "api.py"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# Make the dashboard imports (api.client, utils.config, components.charts) work.
# DASHBOARD_DIR goes first so the dashboard's "api" package is found first.
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

    if not BACKEND_FILE.exists():
        raise FileNotFoundError(
            f"Backend file not found: {BACKEND_FILE.relative_to(ROOT)}. "
            "Edit BACKEND_FILE in streamlit_app.py."
        )

    # api.py looks for the model with relative paths (src/loan_model.pkl),
    # so load it while the working directory is the app folder (same as when you
    # ran "uvicorn src.api:app" from loan-risk-predictor).
    old_cwd = os.getcwd()
    os.chdir(APP_DIR)
    try:
        # Loaded under a different module name so it does not clash with dashboard/api/.
        spec = importlib.util.spec_from_file_location("loan_backend", BACKEND_FILE)
        module = importlib.util.module_from_spec(spec)
        sys.modules["loan_backend"] = module
        spec.loader.exec_module(module)
    finally:
        os.chdir(old_cwd)

    if getattr(module, "model", None) is None:
        raise RuntimeError(
            "src/api.py loaded, but src/loan_model.pkl was not found or could not be read. "
            "Make sure the model file is committed to the repo (not blocked by .gitignore) "
            "and that the scikit-learn/xgboost versions in requirements.txt match the "
            "ones used to train the model."
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
# Frontend: pages are discovered from dashboard/pages/ automatically
# ---------------------------------------------------------------------------
PAGE_ICONS = {
    "Single Prediction": "\U0001F9EE",
    "Batch Scoring": "\U0001F4C2",
    "Explainability SHAP": "\U0001F50D",
    "Model Performance": "\U0001F4CA",
    "Drift Monitoring": "\U0001F4C9",
}


def _page_title(path: Path) -> str:
    """'3_Explainability_SHAP.py' -> 'Explainability SHAP'"""
    name = path.stem
    prefix, sep, rest = name.partition("_")
    if sep and prefix.isdigit():
        name = rest
    return name.replace("_", " ")


def _page_order(path: Path):
    prefix = path.stem.partition("_")[0]
    return (int(prefix) if prefix.isdigit() else 999, path.name)


def _discover_pages():
    pages = [st.Page((DASHBOARD_DIR / "app.py").relative_to(ROOT).as_posix(), title="Home", icon="\U0001F3E0", default=True)]
    if PAGES_DIR.exists():
        for f in sorted(PAGES_DIR.glob("*.py"), key=_page_order):
            if f.name.startswith("_"):
                continue
            # Placeholder files that are still empty are skipped, so the sidebar
            # only shows pages you have actually built.
            if not f.read_text(encoding="utf-8", errors="ignore").strip():
                continue
            title = _page_title(f)
            pages.append(
                st.Page(f.relative_to(ROOT).as_posix(), title=title, icon=PAGE_ICONS.get(title))
            )
    return pages


st.navigation(_discover_pages()).run()