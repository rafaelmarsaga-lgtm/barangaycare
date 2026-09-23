"""Booking rules as pure functions.

"now" is always passed in instead of read from the clock inside, so tests can
check "today at 2:10 PM" or "a Sunday" without faking the system time.
"""
from datetime import date, datetime, time, timedelta, timezone

# The Philippines has no daylight saving time, so a fixed UTC+8 offset is exact
# and avoids needing the tzdata package on Windows.
PH_TZ = timezone(timedelta(hours=8), "Asia/Manila")

# Hourly slots; 12:00 is the lunch break.
SLOTS = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00"]
SERVICES = ["General Check-up", "Prenatal", "Immunization", "Dental"]
STATUSES = ["Booked", "Completed", "No-show"]
FINAL_STATUSES = ["Completed", "No-show"]

SUNDAY = 6  # date.weekday(): Monday = 0 ... Sunday = 6


class BookingError(Exception):
    """A business-rule violation; the router turns it into HTTP 400."""


def now_ph() -> datetime:
    """The single source of "now" for the whole app (timezone-aware, PH time)."""
    return datetime.now(PH_TZ)


def is_closed_day(day: date) -> bool:
    return day.weekday() == SUNDAY


def slot_has_passed(day: date, slot: str, now: datetime) -> bool:
    # A slot that has already started counts as passed: nobody can arrive on time.
    slot_start = datetime.combine(day, time.fromisoformat(slot), tzinfo=PH_TZ)
    return slot_start <= now


def open_slots(day: date, booked_slots: set[str], now: datetime) -> list[str]:
    """Slots that are unbooked AND still bookable, in time order. Shared by the
    slot picker and the daily summary so they can never disagree."""
    if is_closed_day(day):
        return []
    # slot_has_passed is True for every slot on a past date, so past dates give [].
    return [
        slot for slot in SLOTS
        if slot not in booked_slots and not slot_has_passed(day, slot, now)
    ]


def check_bookable(day: date, slot: str, now: datetime) -> None:
    """Raise BookingError if this date/slot can't be booked. Order matters:
    the most general reason is reported first."""
    if day < now.date():
        raise BookingError("Past dates cannot be booked.")
    if is_closed_day(day):
        raise BookingError("The health center is closed on Sundays.")
    if slot_has_passed(day, slot, now):
        raise BookingError("That time slot has already passed today.")


def can_change_status(current: str, new: str) -> bool:
    # One-way flow: only a Booked appointment can be closed out.
    return current == "Booked" and new in FINAL_STATUSES
