from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment
from app.schemas import SummaryOut
from app.services.booking import now_ph
from app.services.summary import build_summary

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("", response_model=SummaryOut)
def daily_summary(
    day: date = Query(alias="date"),
    db: Session = Depends(get_db),
    now: datetime = Depends(now_ph),
):
    # Counts every appointment that day whatever its status: a Completed or
    # No-show visit still used the slot.
    appointments = db.scalars(
        select(Appointment).where(Appointment.appointment_date == day)
    ).all()
    return build_summary(day, appointments, now)
