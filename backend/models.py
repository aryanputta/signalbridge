from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class PatientProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class SignalLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patientprofile.id")
    signal: str
    context_json: Optional[str] = None  # serialized CaregiverContext
    suggested_intent: Optional[str] = None
    confidence: Optional[float] = None
    urgency: Optional[str] = None
    explanation: Optional[str] = None
    confirmed_intent: Optional[str] = None
    feedback: Optional[str] = None  # "correct" | "partial" | "incorrect"
    caregiver_note: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


class PatternSummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patientprofile.id")
    signal: str
    confirmed_intent: str
    count: int = Field(default=1)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    time_buckets: Optional[str] = None  # JSON: {"morning": 3, "afternoon": 1}
