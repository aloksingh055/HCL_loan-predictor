import requests
from utils.config import API_BASE_URL, REQUEST_TIMEOUT


class APIError(Exception):
    """Backend call fail hone par dashboard ko readable error dene ke liye."""


def _request(method: str, path: str, **kwargs):
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    except requests.exceptions.ConnectionError:
        raise APIError("Backend se connect nahi ho paya. Kya FastAPI server chal raha hai?")
    except requests.exceptions.Timeout:
        raise APIError("Backend ne time par response nahi diya.")

    if not response.ok:
        # Tumhara backend error {"detail": "..."} format mein bhejta hai
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise APIError(f"Backend error {response.status_code}: {detail}")

    return response.json()


# ---------------------------------------------------------------------------
# BACKEND API #1: GET /   (health check)
# Response: {"message": "Loan Default Prediction API is running successfully!"}
# ---------------------------------------------------------------------------
def check_health():
    return _request("GET", "/")


# ---------------------------------------------------------------------------
# BACKEND API #2: POST /predict   (single applicant scoring)
# Request body (JSON) ke fields backend ke LoanRequest model se match hone chahiye:
#   Age, Income, LoanAmount, CreditScore, MonthsEmployed, NumCreditLines,
#   InterestRate, LoanTerm, DTIRatio, Education, EmploymentType, MaritalStatus,
#   HasMortgage, HasDependents, LoanPurpose, HasCoSigner
# Response: {"default_probability": float, "prediction": 0 or 1, "risk_status": str}
# ---------------------------------------------------------------------------
def predict_loan_risk(payload: dict):
    return _request("POST", "/predict", json=payload)


# ---------------------------------------------------------------------------
# FUTURE BACKEND APIs (abhi backend mein NAHI hain, jab banao tab yahan add karna)
#
# TODO: POST /predict-batch   -> Batch Scoring page (2_Batch_Scoring.py)
# TODO: POST /explain         -> SHAP page (3_Explainability_SHAP.py)
# TODO: GET  /metrics         -> Model Performance page (4_Model_Performance.py)
# TODO: GET  /drift           -> Drift Monitoring page (5_Drift_Monitoring.py)
# ---------------------------------------------------------------------------