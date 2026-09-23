"""Request/response shapes. Pydantic rejects bad formats (422) before any
endpoint code runs; date rules that depend on "now" live in services/booking.py."""
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.services.booking import FINAL_STATUSES, SERVICES, SLOTS

ServiceName = Literal[tuple(SERVICES)]
TimeSlot = Literal[tuple(SLOTS)]

# strip_whitespace runs first, so "  A  " is checked as "A" (too short).
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
# Exactly 11 digits starting with 09; spaces/dashes are rejected, not cleaned.
ContactNumber = Annotated[str, StringConstraints(pattern=r"^09\d{9}$")]

# Friendly message per field, used by the 422 handler in main.py so the UI
# never shows raw Pydantic text.
FRIENDLY_MESSAGES = {
    "name": "Name must be 2–100 characters.",
    "contact_number": "Contact number must be 11 digits starting with 09.",
    "service": "Please choose a valid service.",
    "appointment_date": "Please choose a valid date.",
    "date": "Please choose a valid date.",
    "time_slot": "Please choose a valid time slot.",
    "status": "Invalid status.",
}
FALLBACK_MESSAGE = "Please check your input."


class AppointmentCreate(BaseModel):
    name: Name
    contact_number: ContactNumber
    service: ServiceName
    appointment_date: date
    time_slot: TimeSlot


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_number: str
    service: str
    appointment_date: date
    time_slot: str
    status: str


class StatusUpdate(BaseModel):
    status: Literal[tuple(FINAL_STATUSES)]


class SlotOut(BaseModel):
    time: str
    available: bool


class SummaryOut(BaseModel):
    date: date
    total: int
    by_service: dict[str, int]
    open_slots: int
