
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent

# All project files and their initial contents
files = {
    "requirements.txt": """
pandas
numpy
scikit-learn
streamlit
fastapi
uvicorn
sqlalchemy
plotly
matplotlib
seaborn
joblib
""",

    "README.md": """
# AI-Powered IT Support Intelligence Platform

## Modules
1. Frontend - Streamlit
2. Backend - FastAPI
3. ML Engine - TF-IDF and Logistic Regression
4. Database - SQLite
5. Analytics - Pandas and Plotly

## Dataset
Place it_support_tickets_v2_master_5000.csv
inside the data folder.
""",

    "frontend/app.py": """
import streamlit as st

st.set_page_config(
    page_title="IT Support Intelligence",
    page_icon="🎫",
    layout="wide"
)

st.title("IT Support Intelligence Platform")
st.write("AI-powered ticket classification and analytics")

st.info("Dashboard initialization successful.")
""",

    "backend/__init__.py": "",
    "backend/main.py": """
from fastapi import FastAPI

app = FastAPI(
    title="IT Support Intelligence API",
    version="1.0"
)

@app.get("/")
def home():
    return {"message": "IT Support API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
""",

    "ml_engine/__init__.py": "",
    "ml_engine/train.py": """
# Model training pipeline will be implemented here.
print("ML training module initialized")
""",

    "ml_engine/predict.py": """
# Ticket prediction module will be implemented here.
print("ML prediction module initialized")
""",

    "database/__init__.py": "",
    "database/db.py": """
from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///./tickets.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

print("Database engine initialized")
""",

    "database/models.py": """
# Database table definitions will be implemented here.
""",

    "analytics/__init__.py": "",
    "analytics/analysis.py": """
# Ticket analytics module will be implemented here.
print("Analytics module initialized")
""",

    ".gitignore": """
venv/
__pycache__/
*.pyc
*.db
.env
"""
}

# Create folders and files
for filename, content in files.items():
    file_path = ROOT / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Created: {filename}")

# Create required folders
for folder in ["data", "models"]:
    (ROOT / folder).mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {folder}")

print("\nProject structure created successfully!")
print(f"Project location: {ROOT}")
