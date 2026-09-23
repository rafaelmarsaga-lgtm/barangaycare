"""API tests for booking. The clock is fixed at Thu 2026-09-24 14:10 (see conftest)."""
import pytest

MONDAY = "2026-09-28"
SUNDAY = "2026-09-27"
TODAY = "2026-09-24"
YESTERDAY = "2026-09-23"


def booking(**overrides):
    body = {
        "name": "Juan Dela Cruz",
        "contact_number": "09171234567",
        "service": "General Check-up",
        "appointment_date": MONDAY,
        "time_slot": "09:00",
    }
    body.update(overrides)
    return body


# --- success -----------------------------------------------------------------

def test_valid_booking_is_created(client):
    response = client.post("/api/appointments", json=booking(name="  Maria Santos  "))
    assert response.status_code == 201
    data = response.json()
    assert data["id"] >= 1
    assert data["name"] == "Maria Santos"  # stored trimmed
    assert data["status"] == "Booked"
    assert data["appointment_date"] == MONDAY
    assert data["time_slot"] == "09:00"


def test_today_with_a_later_slot_is_accepted(client):
    response = client.post("/api/appointments", json=booking(appointment_date=TODAY, time_slot="15:00"))
    assert response.status_code == 201


# --- double booking (409) ----------------------------------------------------

def test_same_slot_twice_is_rejected_with_409(client):
    assert client.post("/api/appointments", json=booking()).status_code == 201
    response = client.post("/api/appointments", json=booking(name="Pedro Reyes", contact_number="09998887777"))
    assert response.status_code == 409
    assert response.json() == {"detail": "That slot is already booked. Please pick another."}


def test_same_slot_on_a_different_day_is_fine(client):
    assert client.post("/api/appointments", json=booking()).status_code == 201
    assert client.post("/api/appointments", json=booking(appointment_date="2026-09-29")).status_code == 201


# --- business rules (400) ----------------------------------------------------

def test_past_date_is_rejected(client):
    response = client.post("/api/appointments", json=booking(appointment_date=YESTERDAY))
    assert response.status_code == 400
    assert response.json() == {"detail": "Past dates cannot be booked."}


def test_sunday_is_rejected(client):
    response = client.post("/api/appointments", json=booking(appointment_date=SUNDAY))
    assert response.status_code == 400
    assert response.json() == {"detail": "The health center is closed on Sundays."}


def test_slot_already_passed_today_is_rejected(client):
    response = client.post("/api/appointments", json=booking(appointment_date=TODAY, time_slot="10:00"))
    assert response.status_code == 400
    assert response.json() == {"detail": "That time slot has already passed today."}


# --- input validation (422 with friendly messages) ---------------------------

CONTACT_MSG = "Contact number must be 11 digits starting with 09."


@pytest.mark.parametrize("contact", [
    "0912345678",     # 10 digits
    "091234567890",   # 12 digits
    "08123456789",    # does not start with 09
    "0917-123-4567",  # dashes
    "0917 1234567",   # space
    "",
])
def test_invalid_contact_numbers_are_rejected(client, contact):
    response = client.post("/api/appointments", json=booking(contact_number=contact))
    assert response.status_code == 422
    assert response.json() == {"detail": CONTACT_MSG}


def test_bad_contact_returns_exactly_the_friendly_message(client):
    response = client.post("/api/appointments", json=booking(contact_number="0912345678"))
    assert response.json() == {"detail": "Contact number must be 11 digits starting with 09."}


@pytest.mark.parametrize("name", [" A ", "   ", "", "x" * 101])
def test_invalid_names_are_rejected(client, name):
    response = client.post("/api/appointments", json=booking(name=name))
    assert response.status_code == 422
    assert response.json() == {"detail": "Name must be 2–100 characters."}


def test_missing_name_gets_the_friendly_name_message(client):
    body = booking()
    del body["name"]
    response = client.post("/api/appointments", json=body)
    assert response.status_code == 422
    assert response.json() == {"detail": "Name must be 2–100 characters."}


def test_invalid_service_returns_friendly_message(client):
    response = client.post("/api/appointments", json=booking(service="Surgery"))
    assert response.status_code == 422
    assert response.json() == {"detail": "Please choose a valid service."}


def test_lunch_hour_is_not_a_valid_slot(client):
    response = client.post("/api/appointments", json=booking(time_slot="12:00"))
    assert response.status_code == 422
    assert response.json() == {"detail": "Please choose a valid time slot."}


def test_invalid_date_returns_friendly_message(client):
    response = client.post("/api/appointments", json=booking(appointment_date="2026-13-01"))
    assert response.status_code == 422
    assert response.json() == {"detail": "Please choose a valid date."}


def test_malformed_body_never_leaks_raw_pydantic_text(client):
    response = client.post("/api/appointments", content="not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Please check your input."}


# --- GET /api/slots ----------------------------------------------------------

def available(response):
    return {slot["time"]: slot["available"] for slot in response.json()}


def test_slots_mark_the_booked_slot_unavailable(client):
    client.post("/api/appointments", json=booking(time_slot="09:00"))
    slots = available(client.get(f"/api/slots?date={MONDAY}"))
    assert slots == {
        "08:00": True, "09:00": False, "10:00": True, "11:00": True,
        "13:00": True, "14:00": True, "15:00": True,
    }


def test_slots_today_after_2pm_leave_only_3pm(client):
    slots = available(client.get(f"/api/slots?date={TODAY}"))
    assert [time for time, is_open in slots.items() if is_open] == ["15:00"]


def test_slots_on_sunday_are_all_unavailable(client):
    slots = available(client.get(f"/api/slots?date={SUNDAY}"))
    assert len(slots) == 7
    assert not any(slots.values())


def test_slots_with_invalid_date_returns_friendly_message(client):
    response = client.get("/api/slots?date=not-a-date")
    assert response.status_code == 422
    assert response.json() == {"detail": "Please choose a valid date."}
