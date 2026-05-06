import json
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from database import get_session
from models import SignalLog, PatientProfile
from suggestion_engine import suggest, record_feedback, _time_bucket, SIGNAL_PRIORS

router = APIRouter(prefix="/signals", tags=["signals"])

VALID_SIGNALS = set(SIGNAL_PRIORS.keys())


class CaregiverContext(BaseModel):
    pain_visible: bool = False
    hours_since_meal: Optional[float] = None
    hours_since_medication: Optional[float] = None
    low_sleep: bool = False
    no_movement: bool = False
    room_temp: Optional[Literal["cold", "hot"]] = None
    caregiver_note: Optional[str] = None
    session_id: Optional[str] = None


class SuggestRequest(BaseModel):
    patient_id: int
    signal: str
    context: CaregiverContext = CaregiverContext()

    @field_validator("signal")
    @classmethod
    def signal_must_be_known(cls, v: str) -> str:
        if v not in VALID_SIGNALS:
            raise ValueError(f"Unknown signal '{v}'. Valid signals: {sorted(VALID_SIGNALS)}")
        return v


class FeedbackRequest(BaseModel):
    log_id: int
    confirmed_intent: str
    feedback: Literal["correct", "partial", "incorrect"]


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

    now = log.timestamp if log.timestamp else datetime.utcnow()
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
