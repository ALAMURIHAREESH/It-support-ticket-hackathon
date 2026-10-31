
from pathlib import Path

project = Path(__file__).resolve().parent
database = project / "database"
database.mkdir(exist_ok=True)

files = {}

files["db.py"] = r'''
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "tickets.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

files["models.py"] = r'''
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text
)
from database.db import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    # Original dataset information
    ticket_id = Column(String(50), unique=True, index=True, nullable=False)
    subject = Column(String(500))
    description = Column(Text)
    ticket_text = Column(Text, nullable=False)

    category = Column(String(100))
    subcategory = Column(String(100))

    priority = Column(String(50))
    impact = Column(String(50))
    urgency = Column(String(50))
    status = Column(String(50))
    channel = Column(String(50))
    assigned_group = Column(String(150))

    resolution_summary = Column(Text)
    first_response_minutes = Column(Float)
    resolution_minutes = Column(Float)
    reopen_count = Column(Integer)
    sla_target_minutes = Column(Float)
    sla_breached = Column(Boolean)

    created_at = Column(DateTime)
    resolved_at = Column(DateTime)

    # ML prediction and workflow information
    predicted_category = Column(String(100))
    confidence = Column(Float)
    decision = Column(String(50))
    routing_status = Column(String(50))
    review_status = Column(String(50), default="NOT_REQUIRED")
    reviewed_category = Column(String(100))
'''

files["init_db.py"] = r'''
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.db import engine, Base
from database import models

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Database initialized successfully!")
print("Database location:", ROOT / "tickets.db")
print("Table created: tickets")
'''

files["seed_database.py"] = r'''
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.db import SessionLocal, engine, Base
from database.models import Ticket

DATA_PATH = ROOT / "data" / "it_support_tickets_v2.csv"

# Initialize tables
Base.metadata.create_all(bind=engine)

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

required_columns = ["ticket_id", "ticket_text", "category"]
missing = [c for c in required_columns if c not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")


def clean_value(value):
    if pd.isna(value):
        return None
    return value


def parse_datetime(value):
    if pd.isna(value):
        return None
    return pd.to_datetime(value).to_pydatetime()


db = SessionLocal()

try:
    inserted = 0
    skipped = 0

    for _, row in df.iterrows():

        ticket_id = str(row["ticket_id"])

        # Avoid duplicate records when seed script is rerun
        existing = db.query(Ticket).filter_by(
            ticket_id=ticket_id
        ).first()

        if existing:
            skipped += 1
            continue

        ticket = Ticket(
            ticket_id=ticket_id,
            subject=clean_value(row.get("subject")),
            description=clean_value(row.get("description")),
            ticket_text=str(row["ticket_text"]),
            category=clean_value(row.get("category")),
            subcategory=clean_value(row.get("subcategory")),
            priority=clean_value(row.get("priority")),
            impact=clean_value(row.get("impact")),
            urgency=clean_value(row.get("urgency")),
            status=clean_value(row.get("status")),
            channel=clean_value(row.get("channel")),
            assigned_group=clean_value(row.get("assigned_group")),
            resolution_summary=clean_value(
                row.get("resolution_summary")
            ),
            first_response_minutes=clean_value(
                row.get("first_response_minutes")
            ),
            resolution_minutes=clean_value(
                row.get("resolution_minutes")
            ),
            reopen_count=clean_value(row.get("reopen_count")),
            sla_target_minutes=clean_value(
                row.get("sla_target_minutes")
            ),
            sla_breached=clean_value(row.get("sla_breached")),
            created_at=parse_datetime(row.get("created_at")),
            resolved_at=parse_datetime(row.get("resolved_at")),
            predicted_category=None,
            confidence=None,
            decision="HISTORICAL",
            routing_status="HISTORICAL",
            review_status="NOT_REQUIRED"
        )

        db.add(ticket)
        inserted += 1

    db.commit()

    print("\nHistorical data imported successfully!")
    print("New records inserted:", inserted)
    print("Existing records skipped:", skipped)

    total = db.query(Ticket).count()
    print("Total tickets in database:", total)

except Exception:
    db.rollback()
    raise

finally:
    db.close()
'''

for filename, content in files.items():
    path = database / filename
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print("Created:", path)

init_file = database / "init_db.py"
seed_file = database / "seed_database.py"

import subprocess
import sys

print("\nInitializing database...")
subprocess.run([sys.executable, str(init_file)], check=True)

print("\nImporting historical tickets...")
subprocess.run([sys.executable, str(seed_file)], check=True)

print("\nDATABASE SETUP COMPLETED!")
