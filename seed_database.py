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
