from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.services.booking import now_ph


class Appointment(Base):
    __tablename__ = "appointments"
    # The database itself refuses a second booking for the same slot, so even two
    # requests arriving at the same instant cannot both succeed.
    __table_args__ = (
        UniqueConstraint("appointment_date", "time_slot", name="uq_date_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    contact_number: Mapped[str] = mapped_column(String(11))
    service: Mapped[str] = mapped_column(String(30))
    appointment_date: Mapped[date] = mapped_column(Date, index=True)
    time_slot: Mapped[str] = mapped_column(String(5))
    status: Mapped[str] = mapped_column(String(10), default="Booked")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_ph)
