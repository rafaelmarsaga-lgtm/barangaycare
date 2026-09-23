from datetime import date, datetime

from app.services.booking import SERVICES, SLOTS, is_closed_day, slot_has_passed


def build_summary(day: date, appointments, now: datetime) -> dict:
    """Daily summary. `appointments` only needs `.service` and `.time_slot`."""
    by_service = {service: 0 for service in SERVICES}  # zeros shown, not missing
    for appointment in appointments:
        by_service[appointment.service] += 1

    return {
        "date": day,
        "total": len(appointments),
        "by_service": by_service,
        "open_slots": count_open_slots(day, appointments, now),
    }


def count_open_slots(day: date, appointments, now: datetime) -> int:
    """Open = unbooked AND still bookable. Reuses the booking rules so the
    summary and the booking form can never disagree."""
    if is_closed_day(day):
        return 0
    booked = {appointment.time_slot for appointment in appointments}
    # slot_has_passed is True for every slot on a past date, so past dates give 0.
    return sum(
        1 for slot in SLOTS
        if slot not in booked and not slot_has_passed(day, slot, now)
    )
