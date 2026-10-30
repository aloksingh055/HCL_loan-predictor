# Loan Default Prediction Using Machine Learning

An ML-driven system that predicts the probability that a loan applicant will default, served through a real-time **FastAPI** scoring service and an interactive **Streamlit** dashboard.

> **Project ID:** P_137 | **Domain:** Banking (Bank Muscat context) | **Category:** Data Analytics
> **Author:** Alok Singh, B.Tech CSE, ABES Engineering College, Ghaziabad (2026-2027)

---

## Project Goals

| Goal | Target |
| --- | --- |
| Model discrimination | AUC-ROC >= 85% on held-out test data |
| Business impact | 30% reduction in NPA (to be estimated through back-testing) |
| Transparency | SHAP-based explanations for every prediction |
| Reliability | Data drift monitoring and experiment tracking |

These are **targets**. Measured results will be added to this README after the models are trained and evaluated.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.11 |
| Modelling | scikit-learn, XGBoost (Logistic Regression, Random Forest, XGBoost) |
| Explainability | SHAP |
| Backend API | FastAPI |
| Dashboard | Streamlit, Plotly, Requests |
| Database | PostgreSQL (planned) |
| MLOps | MLflow, EvidentlyAI (planned) |
| Deployment | Docker, AWS ECS (planned) |

## Current Status

| Component | Status |
| --- | --- |
| FastAPI backend (`GET /`, `POST /predict`) | Done |
| Dashboard: Home page (backend health check) | Done |
| Dashboard: Single Prediction page (form + risk gauge) | Done |
| Dashboard: Batch Scoring, SHAP, Model Performance, Drift Monitoring pages | Placeholder files, not built yet |
| PostgreSQL storage, MLflow, EvidentlyAI | Planned |
| Docker / AWS ECS deployment | Planned |

## Project Structure

```
loan-risk-predictor/
├── dashboard/                      # Streamlit front end
│   ├── app.py                      # Home page + backend health check
│   ├── requirements.txt
│   ├── .env                        # Backend URL (not committed)
│   ├── .streamlit/config.toml
│   ├── api/
│   │   └── client.py               # ALL backend API calls live here
│   ├── pages/
│   │   ├── 1_Single_Prediction.py
│   │   ├── 2_Batch_Scoring.py
│   │   ├── 3_Explainability_SHAP.py
│   │   ├── 4_Model_Performance.py
│   │   └── 5_Drift_Monitoring.py
│   ├── components/
│   │   ├── charts.py               # Risk gauge
│   │   └── metrics.py
│   └── utils/
│       ├── config.py               # Reads API_BASE_URL from .env
│       └── options.py              # Dropdown values for categorical inputs
├── api.py                          # FastAPI backend (loads the trained model)
├── src/loan_model.pkl              # Trained model (loaded by api.py)
└── data/                           # Dataset (not committed)
```

## Backend API

The dashboard talks to the backend only through `dashboard/api/client.py`.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Health check |
| POST | `/predict` | Score a single applicant |

**`POST /predict` request body (16 fields):**

`Age`, `Income`, `LoanAmount`, `CreditScore`, `MonthsEmployed`, `NumCreditLines`, `InterestRate`, `LoanTerm`, `DTIRatio`, `Education`, `EmploymentType`, `MaritalStatus`, `HasMortgage`, `HasDependents`, `LoanPurpose`, `HasCoSigner`

**Response:**

```json
{
  "default_probability": 0.0,
  "prediction": 0,
  "risk_status": "Low Risk (Non-Default)"
}
```

(The values above are only an example of the response shape, not real model output.)

Planned endpoints (not implemented yet): batch scoring, SHAP explanation, model metrics, drift report.

## Getting Started (Windows / PowerShell)

### 1. Create and activate a virtual environment

```powershell
cd loan-risk-predictor
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

### 2. Install dependencies

```powershell
# Dashboard
pip install -r dashboard\requirements.txt

# Backend (FastAPI + model libraries)
pip install fastapi uvicorn pandas joblib scikit-learn
```

Install `xgboost` as well if the saved model uses it.

### 3. Configure the backend URL

Create `dashboard\.env`:

```
API_BASE_URL=http://127.0.0.1:8000
REQUEST_TIMEOUT=10
```

### 4. Start the backend

Run this from the folder that contains `api.py`:

```powershell
uvicorn api:app --reload
```

Open `http://127.0.0.1:8000/docs` to see the interactive API documentation.

### 5. Start the dashboard

In a second terminal (with the virtual environment activated):

```powershell
cd dashboard
streamlit run app.py
```

The dashboard opens in your browser. Use the sidebar to open **Single Prediction**.

## Notes

- The dropdown values in `dashboard/utils/options.py` must match the categories used when the model was trained. Update that file if your dataset uses different values.
- `.env`, `venv/`, `data/` and the local `Postgresql/` folder are excluded from Git through `.gitignore`.

## Roadmap

1. Complete model training and comparison (Logistic Regression, Random Forest, XGBoost) and report measured metrics
2. Add SHAP explainability endpoint and dashboard page
3. Add batch scoring (CSV upload)
4. Add model performance and drift monitoring pages (MLflow, EvidentlyAI)
5. Store predictions in PostgreSQL
6. Containerise with Docker and deploy on AWS ECS

## License

This project is an academic prototype built for educational purposes. Add a license here if you plan to publish it.