"""Unit tests for the pure business rules (no database, no HTTP)."""
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.services.booking import (
    PH_TZ,
    SERVICES,
    SLOTS,
    BookingError,
    can_change_status,
    check_bookable,
    is_closed_day,
    open_slots,
    slot_has_passed,
)
from app.services.summary import build_summary

# Fixed clock: Thursday 24 Sep 2026, 2:10 PM Philippine time.
NOW = datetime(2026, 9, 24, 14, 10, tzinfo=PH_TZ)
TODAY = date(2026, 9, 24)
YESTERDAY = date(2026, 9, 23)
SATURDAY = date(2026, 9, 26)
SUNDAY = date(2026, 9, 27)
MONDAY = date(2026, 9, 28)


def appt(service, slot):
    # build_summary only reads these two attributes, so a plain object is enough.
    return SimpleNamespace(service=service, time_slot=slot)


# --- fixed lists -------------------------------------------------------------

def test_there_are_seven_hourly_slots_with_a_lunch_break():
    assert SLOTS == ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00"]


def test_the_four_services():
    assert SERVICES == ["General Check-up", "Prenatal", "Immunization", "Dental"]


# --- closed days -------------------------------------------------------------

def test_sunday_is_a_closed_day():
    assert is_closed_day(SUNDAY) is True


def test_saturday_is_open():
    assert is_closed_day(SATURDAY) is False


# --- slot_has_passed ---------------------------------------------------------

def test_morning_slot_today_has_passed_in_the_afternoon():
    assert slot_has_passed(TODAY, "08:00", NOW) is True


def test_slot_that_already_started_counts_as_passed():
    # 14:00 started ten minutes ago; nobody can arrive on time for it.
    assert slot_has_passed(TODAY, "14:00", NOW) is True


def test_later_slot_today_has_not_passed():
    assert slot_has_passed(TODAY, "15:00", NOW) is False


def test_every_slot_on_a_future_day_is_still_ahead():
    assert slot_has_passed(MONDAY, "08:00", NOW) is False


# --- check_bookable ----------------------------------------------------------

def test_past_date_is_rejected():
    with pytest.raises(BookingError, match="Past dates cannot be booked."):
        check_bookable(YESTERDAY, "10:00", NOW)


def test_sunday_is_rejected():
    with pytest.raises(BookingError, match="The health center is closed on Sundays."):
        check_bookable(SUNDAY, "10:00", NOW)


def test_today_with_a_passed_slot_is_rejected():
    with pytest.raises(BookingError, match="That time slot has already passed today."):
        check_bookable(TODAY, "09:00", NOW)


def test_today_with_a_future_slot_is_allowed():
    check_bookable(TODAY, "15:00", NOW)  # no exception


def test_future_saturday_is_allowed():
    check_bookable(SATURDAY, "08:00", NOW)  # no exception


# --- status transitions ------------------------------------------------------

def test_booked_can_become_completed():
    assert can_change_status("Booked", "Completed") is True


def test_booked_can_become_no_show():
    assert can_change_status("Booked", "No-show") is True


def test_completed_is_final():
    assert can_change_status("Completed", "No-show") is False


def test_no_show_is_final():
    assert can_change_status("No-show", "Completed") is False


# --- open_slots (shared by /api/slots and the summary) -----------------------

def test_open_slots_lists_unbooked_future_slots_in_order():
    assert open_slots(MONDAY, {"09:00", "13:00"}, NOW) == ["08:00", "10:00", "11:00", "14:00", "15:00"]


def test_open_slots_today_after_2pm():
    assert open_slots(TODAY, set(), NOW) == ["15:00"]


def test_open_slots_on_sunday_is_empty():
    assert open_slots(SUNDAY, set(), NOW) == []


# --- build_summary -----------------------------------------------------------

def test_summary_counts_per_service_with_zeros_filled_in():
    appts = [
        appt("Dental", "08:00"),
        appt("Dental", "09:00"),
        appt("Prenatal", "10:00"),
    ]
    summary = build_summary(MONDAY, appts, NOW)
    assert summary["date"] == MONDAY
    assert summary["total"] == 3
    assert summary["by_service"] == {
        "General Check-up": 0,
        "Prenatal": 1,
        "Immunization": 0,
        "Dental": 2,
    }


def test_open_slots_on_a_future_weekday_are_the_unbooked_ones():
    appts = [appt("Dental", "08:00"), appt("Prenatal", "13:00")]
    assert build_summary(MONDAY, appts, NOW)["open_slots"] == 5


def test_open_slots_today_after_2pm_leave_only_the_3pm_slot():
    assert build_summary(TODAY, [], NOW)["open_slots"] == 1


def test_open_slots_today_after_2pm_are_zero_when_3pm_is_booked():
    appts = [appt("Immunization", "15:00")]
    assert build_summary(TODAY, appts, NOW)["open_slots"] == 0


def test_booked_morning_slot_today_is_not_double_subtracted():
    # 08:00 is both booked and passed; it must be removed only once.
    appts = [appt("Dental", "08:00")]
    summary = build_summary(TODAY, appts, NOW)
    assert summary["total"] == 1
    assert summary["open_slots"] == 1


def test_sunday_has_zero_open_slots():
    assert build_summary(SUNDAY, [], NOW)["open_slots"] == 0


def test_past_date_has_zero_open_slots():
    assert build_summary(YESTERDAY, [], NOW)["open_slots"] == 0
