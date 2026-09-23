from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment
from app.schemas import AppointmentCreate, AppointmentOut, StatusUpdate
from app.services.booking import BookingError, can_change_status, check_bookable, now_ph

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    day: date = Query(alias="date"),  # "date" in the URL; renamed here to avoid shadowing the type
    db: Session = Depends(get_db),
):
    # "HH:MM" strings sort correctly as text, so ordering by time_slot is time order.
    return db.scalars(
        select(Appointment)
        .where(Appointment.appointment_date == day)
        .order_by(Appointment.time_slot)
    ).all()


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


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
def update_status(appointment_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if not can_change_status(appointment.status, payload.status):
        raise HTTPException(status_code=400, detail="Status is already final.")
    appointment.status = payload.status
    db.commit()
    db.refresh(appointment)
    return appointment
