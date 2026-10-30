import streamlit as st
from api.client import check_health, APIError

st.set_page_config(page_title="Loan Risk Dashboard", layout="wide")
st.title("Loan Risk Prediction Dashboard")

# >>> BACKEND API CALL: GET /  (health check)
try:
    check_health()
    st.success("Backend connected")
except APIError as e:
    st.error(str(e))

st.write("Left sidebar se **Single Prediction** page kholo.")