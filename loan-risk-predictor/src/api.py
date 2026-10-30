from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os


# FastAPI app initialize karna
app = FastAPI(
    title="Loan Default Prediction API",
    description="Real-time loan risk scoring API for banking domain",
    version="1.0"
)

# Model load karna
model_path = "../src/loan_model.pkl"
if not os.path.exists(model_path):
    model_path = "src/loan_model.pkl"
if not os.path.exists(model_path):
    model_path = "loan_model.pkl"

try:
    model = joblib.load(model_path)
except Exception as e:
    model = None

# Request body structure define karna
class LoanRequest(BaseModel):
    Age: int
    Income: int
    LoanAmount: int
    CreditScore: int
    MonthsEmployed: int
    NumCreditLines: int
    InterestRate: float
    LoanTerm: int
    DTIRatio: float
    Education: str
    EmploymentType: str
    MaritalStatus: str
    HasMortgage: str
    HasDependents: str
    LoanPurpose: str
    HasCoSigner: str

@app.get("/")
def home():
    return {"message": "Loan Default Prediction API is running successfully!"}

@app.post("/predict")
def predict_default(data: LoanRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model file not found on server.")
    
    try:
        # Input data ko DataFrame mein convert karna
        input_data = pd.DataFrame([data.dict()])
        
        # Training data ki tarah dummy variables banana
        input_encoded = pd.get_dummies(input_data, drop_first=True)
        
        # Model ke original features ke sath align karna
        model_features = getattr(model, "feature_names_in_", None)
        if model_features is not None:
            input_encoded = input_encoded.reindex(columns=model_features, fill_value=0)
            
        # Probability aur prediction calculate karna
        default_prob = float(model.predict_proba(input_encoded)[:, 1][0])
        prediction = int(model.predict(input_encoded)[0])
        
        risk_status = "High Risk (Default)" if prediction == 1 else "Low Risk (Non-Default)"
        
        return {
            "default_probability": round(default_prob, 4),
            "prediction": prediction,
            "risk_status": risk_status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

