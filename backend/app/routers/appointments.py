from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment
from app.schemas import AppointmentCreate, AppointmentOut
from app.services.booking import BookingError, check_bookable, now_ph

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    now: datetime = Depends(now_ph),
):
    try:
        check_bookable(payload.appointment_date, payload.time_slot, now)
    except BookingError as error:
        raise HTTPException(status_code=400, detail=str(error))

    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        # No "is it free?" SELECT first: the UNIQUE(date, slot) constraint is the
        # single check, so two simultaneous requests can't both get the slot.
        db.rollback()
        raise HTTPException(status_code=409, detail="That slot is already booked. Please pick another.")
    db.refresh(appointment)
    return appointment
