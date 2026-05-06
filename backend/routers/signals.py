import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import SignalLog, PatientProfile
from suggestion_engine import suggest, record_feedback, _time_bucket

router = APIRouter(prefix="/signals", tags=["signals"])


class CaregiverContext(BaseModel):
    pain_visible: bool = False
    hours_since_meal: Optional[float] = None
    hours_since_medication: Optional[float] = None
    low_sleep: bool = False
    no_movement: bool = False
    room_temp: Optional[str] = None  # "cold" | "hot" | None
    caregiver_note: Optional[str] = None
    session_id: Optional[str] = None


class SuggestRequest(BaseModel):
    patient_id: int
    signal: str
    context: CaregiverContext = CaregiverContext()


class FeedbackRequest(BaseModel):
    log_id: int
    confirmed_intent: str
    feedback: str  # "correct" | "partial" | "incorrect"


@router.post("/suggest")
def get_suggestion(req: SuggestRequest, session: Session = Depends(get_session)):
    patient = session.get(PatientProfile, req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    context_dict = req.context.model_dump(exclude={"caregiver_note", "session_id"})
    now = datetime.utcnow()
    result = suggest(req.signal, req.patient_id, context_dict, session, now)

    top = result["predictions"][0] if result["predictions"] else {}
    log = SignalLog(
        patient_id=req.patient_id,
        signal=req.signal,
        context_json=json.dumps(req.context.model_dump()),
        suggested_intent=top.get("intent"),
        confidence=top.get("confidence"),
        urgency=result.get("urgency"),
        explanation=top.get("explanation"),
        caregiver_note=req.context.caregiver_note,
        session_id=req.context.session_id,
        timestamp=now,
    )
    session.add(log)
    session.commit()
    session.refresh(log)

    return {"log_id": log.id, **result}


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, session: Session = Depends(get_session)):
    log = session.get(SignalLog, req.log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Signal log not found")

    context_data = json.loads(log.context_json or "{}")
    now = datetime.fromisoformat(log.timestamp.isoformat()) if log.timestamp else datetime.utcnow()
    time_bucket = _time_bucket(now)

    record_feedback(
        log_id=req.log_id,
        confirmed_intent=req.confirmed_intent,
        feedback=req.feedback,
        patient_id=log.patient_id,
        signal=log.signal,
        time_bucket=time_bucket,
        session=session,
    )

    return {"status": "ok", "confirmed_intent": req.confirmed_intent}


@router.get("/history/{patient_id}")
def get_history(patient_id: int, limit: int = 50, session: Session = Depends(get_session)):
    logs = session.exec(
        select(SignalLog)
        .where(SignalLog.patient_id == patient_id)
        .order_by(SignalLog.timestamp.desc())
        .limit(limit)
    ).all()
    return logs
