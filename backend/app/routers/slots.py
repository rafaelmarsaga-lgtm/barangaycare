from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment
from app.schemas import SlotOut
from app.services.booking import SLOTS, now_ph, open_slots

router = APIRouter(prefix="/api/slots", tags=["slots"])


@router.get("", response_model=list[SlotOut])
def list_slots(
    day: date = Query(alias="date"),  # "date" in the URL; renamed here to avoid shadowing the type
    db: Session = Depends(get_db),
    now: datetime = Depends(now_ph),
):
    booked = set(db.scalars(
        select(Appointment.time_slot).where(Appointment.appointment_date == day)
    ))
    still_open = open_slots(day, booked, now)
    return [{"time": slot, "available": slot in still_open} for slot in SLOTS]
