from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import PatientProfile

router = APIRouter(prefix="/patients", tags=["patients"])


class CreatePatient(BaseModel):
    name: str
    notes: str = ""


@router.post("/")
def create_patient(req: CreatePatient, session: Session = Depends(get_session)):
    patient = PatientProfile(name=req.name, notes=req.notes)
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


@router.get("/")
def list_patients(session: Session = Depends(get_session)):
    return session.exec(select(PatientProfile)).all()


@router.get("/{patient_id}")
def get_patient(patient_id: int, session: Session = Depends(get_session)):
    patient = session.get(PatientProfile, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
