"""API tests for the staff side. The clock is fixed at Thu 2026-09-24 14:10 (see conftest)."""
import pytest

TODAY = "2026-09-24"
SUNDAY = "2026-09-27"
MONDAY = "2026-09-28"
TUESDAY = "2026-09-29"


def book(client, day=MONDAY, slot="09:00", service="General Check-up", name="Juan Dela Cruz"):
    response = client.post("/api/appointments", json={
        "name": name,
        "contact_number": "09171234567",
        "service": service,
        "appointment_date": day,
        "time_slot": slot,
    })
    assert response.status_code == 201, response.text
    return response.json()


def set_status(client, appointment_id, status):
    return client.patch(f"/api/appointments/{appointment_id}/status", json={"status": status})


# --- GET /api/appointments?date= ---------------------------------------------

def test_list_is_filtered_by_date_and_sorted_by_slot(client):
    book(client, MONDAY, "13:00", name="Afternoon Patient")
    book(client, MONDAY, "08:00", name="Morning Patient")
    book(client, TUESDAY, "09:00", name="Other Day")

    response = client.get(f"/api/appointments?date={MONDAY}")
    assert response.status_code == 200
    rows = response.json()
    assert [row["time_slot"] for row in rows] == ["08:00", "13:00"]
    assert [row["name"] for row in rows] == ["Morning Patient", "Afternoon Patient"]


def test_list_for_a_date_with_no_bookings_is_empty(client):
    response = client.get(f"/api/appointments?date={TUESDAY}")
    assert response.status_code == 200
    assert response.json() == []


def test_list_with_invalid_date_returns_friendly_message(client):
    response = client.get("/api/appointments?date=2026-02-30")
    assert response.status_code == 422
    assert response.json() == {"detail": "Please choose a valid date."}


# --- PATCH /api/appointments/{id}/status -------------------------------------

def test_booked_can_be_marked_completed(client):
    appointment = book(client)
    response = set_status(client, appointment["id"], "Completed")
    assert response.status_code == 200
    assert response.json()["status"] == "Completed"
    # And it is really saved, not just echoed back.
    listed = client.get(f"/api/appointments?date={MONDAY}").json()
    assert listed[0]["status"] == "Completed"


def test_booked_can_be_marked_no_show(client):
    appointment = book(client)
    response = set_status(client, appointment["id"], "No-show")
    assert response.status_code == 200
    assert response.json()["status"] == "No-show"


def test_final_status_cannot_be_changed_again(client):
    appointment = book(client)
    set_status(client, appointment["id"], "Completed")
    response = set_status(client, appointment["id"], "No-show")
    assert response.status_code == 400
    assert response.json() == {"detail": "Status is already final."}


def test_unknown_appointment_returns_404(client):
    response = set_status(client, 999, "Completed")
    assert response.status_code == 404
    assert response.json() == {"detail": "Appointment not found."}


@pytest.mark.parametrize("status", ["Booked", "Cancelled", "completed", ""])
def test_invalid_status_returns_friendly_message(client, status):
    appointment = book(client)
    response = set_status(client, appointment["id"], status)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid status."}


# --- GET /api/summary?date= --------------------------------------------------

def test_summary_for_a_future_weekday(client):
    book(client, MONDAY, "08:00", "Dental")
    book(client, MONDAY, "09:00", "Dental")
    book(client, MONDAY, "10:00", "Prenatal")

    response = client.get(f"/api/summary?date={MONDAY}")
    assert response.status_code == 200
    assert response.json() == {
        "date": MONDAY,
        "total": 3,
        "by_service": {"General Check-up": 0, "Prenatal": 1, "Immunization": 0, "Dental": 2},
        "open_slots": 4,
    }


def test_summary_counts_completed_and_no_show_appointments(client):
    first = book(client, MONDAY, "08:00")
    second = book(client, MONDAY, "09:00")
    set_status(client, first["id"], "Completed")
    set_status(client, second["id"], "No-show")

    summary = client.get(f"/api/summary?date={MONDAY}").json()
    assert summary["total"] == 2
    assert summary["open_slots"] == 5  # a No-show still occupies its slot


def test_summary_for_sunday_has_zero_open_slots(client):
    summary = client.get(f"/api/summary?date={SUNDAY}").json()
    assert summary["total"] == 0
    assert summary["open_slots"] == 0


def test_summary_for_today_after_2pm_counts_only_later_unbooked_slots(client):
    assert client.get(f"/api/summary?date={TODAY}").json()["open_slots"] == 1  # only 15:00

    book(client, TODAY, "15:00", "Immunization")
    summary = client.get(f"/api/summary?date={TODAY}").json()
    assert summary["total"] == 1
    assert summary["by_service"]["Immunization"] == 1
    assert summary["open_slots"] == 0


def test_summary_with_invalid_date_returns_friendly_message(client):
    response = client.get("/api/summary?date=yesterday")
    assert response.status_code == 422
    assert response.json() == {"detail": "Please choose a valid date."}
