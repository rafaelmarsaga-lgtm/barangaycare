"""Reset the database and fill it with sample appointments for demos.

Run from the backend folder:  python seed_data.py

Dates are relative to today, so the demo always has upcoming bookings:
the last open day before today (with Completed / No-show history) and the
next three open days. Sundays are skipped, like real bookings.
"""
from datetime import date, timedelta

from app import models  # noqa: F401  (registers the table before create_all)
from app.database import Base, SessionLocal, engine
from app.models import Appointment
from app.schemas import AppointmentCreate
from app.services.booking import is_closed_day, now_ph


def open_days_after(start: date, count: int) -> list[date]:
    days, day = [], start
    while len(days) < count:
        day += timedelta(days=1)
        if not is_closed_day(day):
            days.append(day)
    return days


def previous_open_day(start: date) -> date:
    day = start - timedelta(days=1)
    while is_closed_day(day):
        day -= timedelta(days=1)
    return day


def sample_rows(today: date) -> list[dict]:
    past = previous_open_day(today)
    day1, day2, day3 = open_days_after(today, 3)
    return [
        # Past day: shows finished statuses in the staff view.
        dict(day=past, slot="08:00", name="Lorna Villanueva", contact="09171112233", service="General Check-up", status="Completed"),
        dict(day=past, slot="10:00", name="Carlo Mendoza", contact="09182223344", service="Dental", status="No-show"),
        # Next open day: a busy morning.
        dict(day=day1, slot="08:00", name="Maria Santos", contact="09193334455", service="Prenatal"),
        dict(day=day1, slot="09:00", name="Jose Rizal Bautista", contact="09204445566", service="General Check-up"),
        dict(day=day1, slot="10:00", name="Ana Reyes", contact="09215556677", service="Immunization"),
        dict(day=day1, slot="13:00", name="Pedro Garcia", contact="09226667788", service="Dental"),
        # Following days.
        dict(day=day2, slot="09:00", name="Rosa Dela Cruz", contact="09237778899", service="Prenatal"),
        dict(day=day2, slot="14:00", name="Miguel Torres", contact="09248889900", service="Immunization"),
        dict(day=day3, slot="11:00", name="Elena Ramos", contact="09259990011", service="General Check-up"),
    ]


def seed() -> int:
    Base.metadata.create_all(bind=engine)
    rows = sample_rows(now_ph().date())
    with SessionLocal() as db:
        db.query(Appointment).delete()
        for row in rows:
            # Run each row through the real schema so sample data can't break the rules.
            data = AppointmentCreate(
                name=row["name"], contact_number=row["contact"], service=row["service"],
                appointment_date=row["day"], time_slot=row["slot"],
            )
            db.add(Appointment(**data.model_dump(), status=row.get("status", "Booked")))
        db.commit()
    return len(rows)


if __name__ == "__main__":
    count = seed()
    print(f"Seeded {count} appointments.")
