from pydantic import BaseModel, Field
from typing import Optional


class TicketCreate(BaseModel):
    ticket_text: str = Field(min_length=5)
    subject: Optional[str] = None
    priority: Optional[str] = None
    impact: Optional[str] = None
    urgency: Optional[str] = None
    channel: Optional[str] = None


class TicketReview(BaseModel):
    reviewed_category: str = Field(min_length=1)
