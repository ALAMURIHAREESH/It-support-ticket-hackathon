import sys
from pathlib import Path
from datetime import datetime, date
from uuid import uuid4
from collections import Counter

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.db import get_db, engine, Base
from database import models
from database.models import Ticket
from backend.schemas import TicketCreate, TicketReview
from ml_engine.predict import predict_ticket
from backend.routing import route_ticket

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IT Support Intelligence API",
    description="AI-powered IT support ticket classification, routing and analytics",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "application": "IT Support Intelligence",
        "message": "Backend API is running",
        "documentation": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/tickets")
def create_ticket(
    request: TicketCreate,
    db: Session = Depends(get_db)
    


    
):
    try:
        # Predict ticket category
        prediction = predict_ticket(request.ticket_text)
        similarity=prediction["similarity"],
        issue_status=prediction["issue_status"],
        explanation=prediction["explanation"],

        category = prediction["predicted_category"]
        confidence = prediction["confidence"]
        decision = prediction["decision"]

        # Route only if confidence is above threshold
        if decision == "AUTO_CLASSIFY":
            routing = route_ticket(category)
            assigned_group = routing["assigned_group"]
            routing_status = routing["routing_status"]
            review_status = "NOT_REQUIRED"
        else:
            assigned_group = None
            routing_status = "NOT_ROUTED"
            review_status = "PENDING"

        ticket_id = "ITS-" + uuid4().hex[:10].upper()

        ticket = Ticket(
            ticket_id=ticket_id,
            subject=request.subject,
            description=request.ticket_text,
            ticket_text=request.ticket_text,
            category=None,
            priority=request.priority,
            impact=request.impact,
            urgency=request.urgency,
            channel=request.channel,
            assigned_group=assigned_group,
            created_at=datetime.utcnow(),
            predicted_category=category,
            confidence=confidence,
            decision=decision,
            routing_status=routing_status,
            review_status=review_status,

           # Open-set detection information
            similarity=prediction["similarity"],
            issue_status=prediction["issue_status"],
            explanation=prediction["explanation"]
)
        

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return {
            "ticket_id": ticket.ticket_id,
            "predicted_category": category,
            "confidence": prediction["confidence_percentage"],
            "decision": decision,
            "assigned_group": assigned_group,
            "routing_status": routing_status,
            "review_status": review_status,
            "similarity": prediction["similarity"],
            "issue_status": prediction["issue_status"],
            "explanation": prediction["explanation"],

            "category_probabilities": prediction["category_probabilities"]
}
            
        

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save ticket.")
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/tickets")
def get_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    tickets = (
        db.query(Ticket)
        .order_by(Ticket.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "count": len(tickets),
        "tickets": [
            {
                "ticket_id": t.ticket_id,
                "ticket_text": t.ticket_text,
                "actual_category": t.category,
                "predicted_category": t.predicted_category,
                "confidence": t.confidence,
                "priority": t.priority,
                "assigned_group": t.assigned_group,
                "decision": t.decision,
                "routing_status": t.routing_status,
                "review_status": t.review_status,

# Open-set detection fields
                "similarity": t.similarity,
                "issue_status": t.issue_status,
                "explanation": t.explanation,

                "status": t.status,
                "created_at": t.created_at
            }
            for t in tickets
        ]
    }


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(
        Ticket.ticket_id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket_id": ticket.ticket_id,
        "ticket_text": ticket.ticket_text,
        "actual_category": ticket.category,
        "predicted_category": ticket.predicted_category,
        "confidence": ticket.confidence,
        "assigned_group": ticket.assigned_group,
        "decision": ticket.decision,
        "routing_status": ticket.routing_status,
        "review_status": ticket.review_status,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at
        ,
        "issue_status": ticket.issue_status,
        "explanation": ticket.explanation,
    }


@app.put("/tickets/{ticket_id}/review")
def review_ticket(
    ticket_id: str,
    request: TicketReview,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.ticket_id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.review_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Ticket is not awaiting manual review"
        )

    routing = route_ticket(request.reviewed_category)

    ticket.reviewed_category = request.reviewed_category
    ticket.predicted_category = request.reviewed_category
    ticket.assigned_group = routing["assigned_group"]
    ticket.decision = "MANUALLY_CLASSIFIED"
    ticket.routing_status = routing["routing_status"]
    ticket.review_status = "APPROVED"

    db.commit()
    db.refresh(ticket)

    return {
        "ticket_id": ticket.ticket_id,
        "reviewed_category": ticket.reviewed_category,
        "assigned_group": ticket.assigned_group,
        "review_status": ticket.review_status,
        "routing_status": ticket.routing_status
    }


@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    total = db.query(Ticket).count()

    pending = db.query(Ticket).filter(
        Ticket.review_status == "PENDING"
    ).count()

    routed = db.query(Ticket).filter(
        Ticket.routing_status == "ROUTED"
    ).count()

    sla_breached = db.query(Ticket).filter(
        Ticket.sla_breached.is_(True)
    ).count()

    return {
        "total_tickets": total,
        "routed_tickets": routed,
        "pending_manual_review": pending,
        "sla_breached_tickets": sla_breached
    }


@app.get("/analytics/categories")
def category_analytics(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.coalesce(Ticket.category, Ticket.predicted_category),
            func.count(Ticket.id)
        )
        .filter(
            func.coalesce(Ticket.category, Ticket.predicted_category).isnot(None)
        )
        .group_by(
            func.coalesce(Ticket.category, Ticket.predicted_category)
        )
        .all()
    )

    return {
        "categories": [
            {"category": category, "count": count}
            for category, count in rows
        ]
    }


@app.get("/analytics/trends")
def ticket_trends(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.date(Ticket.created_at),
            func.count(Ticket.id)
        )
        .filter(Ticket.created_at.isnot(None))
        .group_by(func.date(Ticket.created_at))
        .order_by(func.date(Ticket.created_at))
        .all()
    )

    return {
        "daily_ticket_counts": [
            {"date": str(day), "count": count}
            for day, count in rows
        ]
    }
