from datetime import date, datetime

from app.services.booking import SERVICES, open_slots


def build_summary(day: date, appointments, now: datetime) -> dict:
    """Daily summary. `appointments` only needs `.service` and `.time_slot`."""
    by_service = {service: 0 for service in SERVICES}  # zeros shown, not missing
    for appointment in appointments:
        by_service[appointment.service] += 1

    booked = {appointment.time_slot for appointment in appointments}
    return {
        "date": day,
        "total": len(appointments),
        "by_service": by_service,
        "open_slots": len(open_slots(day, booked, now)),
    }
