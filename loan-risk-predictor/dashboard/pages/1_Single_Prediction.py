import streamlit as st

from api.client import predict_loan_risk, APIError
from components.charts import risk_gauge
from utils.options import (
    EDUCATION, EMPLOYMENT_TYPE, MARITAL_STATUS, YES_NO, LOAN_PURPOSE,
)

st.set_page_config(page_title="Single Prediction", layout="wide")
st.title("Single Applicant Risk Prediction")

with st.form("loan_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        age = st.number_input("Age", min_value=18, max_value=100, value=35, step=1)
        income = st.number_input("Income", min_value=0, value=50000, step=1000)
        loan_amount = st.number_input("Loan Amount", min_value=0, value=100000, step=1000)
        credit_score = st.number_input("Credit Score", min_value=300, max_value=850, value=650, step=1)
        months_employed = st.number_input("Months Employed", min_value=0, value=36, step=1)

    with col2:
        num_credit_lines = st.number_input("Number of Credit Lines", min_value=0, value=3, step=1)
        interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=10.0, step=0.1)
        loan_term = st.number_input("Loan Term (months)", min_value=1, value=36, step=1)
        dti_ratio = st.number_input("DTI Ratio", min_value=0.0, max_value=1.0, value=0.4, step=0.01)
        education = st.selectbox("Education", EDUCATION)

    with col3:
        employment_type = st.selectbox("Employment Type", EMPLOYMENT_TYPE)
        marital_status = st.selectbox("Marital Status", MARITAL_STATUS)
        has_mortgage = st.selectbox("Has Mortgage", YES_NO)
        has_dependents = st.selectbox("Has Dependents", YES_NO)
        loan_purpose = st.selectbox("Loan Purpose", LOAN_PURPOSE)
        has_cosigner = st.selectbox("Has Co-Signer", YES_NO)

    submitted = st.form_submit_button("Predict Risk")

if submitted:
    # Keys backend ke LoanRequest model se exactly match hoti hain
    payload = {
        "Age": int(age),
        "Income": int(income),
        "LoanAmount": int(loan_amount),
        "CreditScore": int(credit_score),
        "MonthsEmployed": int(months_employed),
        "NumCreditLines": int(num_credit_lines),
        "InterestRate": float(interest_rate),
        "LoanTerm": int(loan_term),
        "DTIRatio": float(dti_ratio),
        "Education": education,
        "EmploymentType": employment_type,
        "MaritalStatus": marital_status,
        "HasMortgage": has_mortgage,
        "HasDependents": has_dependents,
        "LoanPurpose": loan_purpose,
        "HasCoSigner": has_cosigner,
    }

    try:
        # >>> BACKEND API CALL: POST /predict (api/client.py -> predict_loan_risk)
        result = predict_loan_risk(payload)
    except APIError as e:
        st.error(str(e))
    else:
        is_high_risk = result["prediction"] == 1
        left, right = st.columns([1, 1])
        with left:
            st.plotly_chart(
                risk_gauge(result["default_probability"], is_high_risk),
                use_container_width=True,
            )
        with right:
            if is_high_risk:
                st.error(result["risk_status"])
            else:
                st.success(result["risk_status"])
            st.metric("Default Probability", f"{result['default_probability']:.2%}")
            st.metric("Prediction (0/1)", result["prediction"])