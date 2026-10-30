import os
from dotenv import load_dotenv

load_dotenv()

# Backend FastAPI ka base URL (.env se aata hai)
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))