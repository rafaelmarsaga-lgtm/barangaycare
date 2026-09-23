import { createAppointment, getAppointments, getSlots, getSummary, updateStatus } from "./api.js";
import {
  clearFieldErrors, formatDate, formatSlot, hideAlert, renderAppointments, renderListSkeleton,
  renderSlotSkeleton, renderSlots, renderSummary, setButtonLoading, showAlert, showFieldError,
} from "./ui.js";

// Same rules as the server (schemas.py / booking.py), checked here only so
// residents get instant feedback. The server stays the authority.
const CONTACT_PATTERN = /^09\d{9}$/;

const $ = (id) => document.getElementById(id);

const form = $("booking-form");
const formAlert = $("form-alert");
const dateInput = $("appointment_date");
const slotsBox = $("slots");
const slotsStatus = $("slots-status");
const submitBtn = $("submit-btn");
const submitSpinner = $("submit-spinner");
const submitLabel = $("submit-label");
const successBox = $("booking-success");

// ---------------------------------------------------------------- helpers

function todayISO() {
  // Local date parts, not toISOString() (which is UTC and can be yesterday in PH before 8 AM).
  const now = new Date();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${mm}-${dd}`;
}

function isSunday(isoDate) {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).getDay() === 0;
}

// ---------------------------------------------------------------- tabs

const tabs = [...document.querySelectorAll('[role="tab"]')];

function selectTab(tab) {
  for (const t of tabs) {
    const selected = t === tab;
    t.setAttribute("aria-selected", String(selected));
    t.tabIndex = selected ? 0 : -1;
    t.classList.toggle("bg-brand-700", selected);
    t.classList.toggle("text-white", selected);
    t.classList.toggle("text-brand-700", !selected);
    t.classList.toggle("hover:bg-brand-50", !selected);
    $(t.getAttribute("aria-controls")).hidden = !selected;
  }
  // Refresh on every visit so bookings made in the other tab show up.
  if (tab.id === "tab-staff") loadStaff();
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTab(tab));
  // Arrow keys move between tabs (standard ARIA tabs keyboard pattern).
  tab.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    const step = event.key === "ArrowRight" ? 1 : -1;
    const next = tabs[(index + step + tabs.length) % tabs.length];
    selectTab(next);
    next.focus();
  });
});

// ---------------------------------------------------------------- slots

let slotRequest = 0; // ignore responses from an older date if the user changes it quickly

async function loadSlots() {
  const date = dateInput.value;
  slotsBox.replaceChildren();

  if (!date) {
    slotsStatus.textContent = "Choose a date first to see open slots.";
    return;
  }
  if (isSunday(date)) {
    slotsStatus.textContent = "The health center is closed on Sundays. Please choose another day.";
    return;
  }

  const requestId = ++slotRequest;
  slotsStatus.textContent = "Loading open slots…";
  renderSlotSkeleton(slotsBox);
  try {
    const slots = await getSlots(date);
    if (requestId !== slotRequest) return;
    renderSlots(slotsBox, slots);
    const openCount = slots.filter((s) => s.available).length;
    slotsStatus.textContent = openCount === 0
      ? "No open slots left on this date. Please choose another day."
      : `${openCount} of ${slots.length} slots open on ${formatDate(date)}.`;
  } catch (error) {
    if (requestId !== slotRequest) return;
    slotsBox.replaceChildren();
    slotsStatus.textContent = error.message;
  }
}

dateInput.addEventListener("change", () => {
  $("appointment_date-error").hidden = true;
  loadSlots();
});

// ---------------------------------------------------------------- validation

function readForm() {
  const data = new FormData(form);
  return {
    name: (data.get("name") || "").trim(),
    contact_number: (data.get("contact_number") || "").trim(),
    service: data.get("service") || "",
    appointment_date: data.get("appointment_date") || "",
    time_slot: data.get("time_slot") || "",
  };
}

/** Returns {field: message} for every problem, in form order. */
function validate(values) {
  const errors = {};
  if (values.name.length < 2 || values.name.length > 100) {
    errors.name = "Name must be 2–100 characters.";
  }
  if (!CONTACT_PATTERN.test(values.contact_number)) {
    errors.contact_number = "Contact number must be 11 digits starting with 09.";
  }
  if (!values.service) errors.service = "Please choose a service.";
  if (!values.appointment_date) {
    errors.appointment_date = "Please choose a date.";
  } else if (values.appointment_date < todayISO()) {
    errors.appointment_date = "Past dates cannot be booked.";
  } else if (isSunday(values.appointment_date)) {
    errors.appointment_date = "The health center is closed on Sundays.";
  }
  if (!values.time_slot && !errors.appointment_date) {
    errors.time_slot = "Please choose a time slot.";
  }
  return errors;
}

// ---------------------------------------------------------------- submit

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearFieldErrors(form);
  hideAlert(formAlert);

  const values = readForm();
  const errors = validate(values);
  const fields = Object.keys(errors);
  if (fields.length > 0) {
    fields.forEach((field) => showFieldError(field, errors[field]));
    // Move focus to the first problem so keyboard and screen-reader users land on it.
    const first = fields[0] === "time_slot" ? slotsBox.querySelector("input:not(:disabled)") : $(fields[0]);
    (first || $(fields[0]) || formAlert).focus();
    return;
  }

  setButtonLoading(submitBtn, submitSpinner, submitLabel, true, "Booking…");
  try {
    const appointment = await createAppointment(values);
    showSuccess(appointment);
  } catch (error) {
    showAlert(formAlert, error.message);
    formAlert.scrollIntoView({ block: "nearest" });
    // Someone else may have taken the slot: refresh so it shows as unavailable.
    if (error.status === 409) loadSlots();
  } finally {
    setButtonLoading(submitBtn, submitSpinner, submitLabel, false, "Book appointment");
  }
});

function showSuccess(appointment) {
  $("ok-id").textContent = `#${appointment.id}`;
  $("ok-name").textContent = appointment.name;
  $("ok-service").textContent = appointment.service;
  $("ok-when").textContent = `${formatDate(appointment.appointment_date)}, ${formatSlot(appointment.time_slot)}`;
  form.hidden = true;
  successBox.hidden = false;
  successBox.focus();
}

$("book-another").addEventListener("click", () => {
  form.reset();
  clearFieldErrors(form);
  hideAlert(formAlert);
  slotsBox.replaceChildren();
  slotsStatus.textContent = "Choose a date first to see open slots.";
  successBox.hidden = true;
  form.hidden = false;
  $("name").focus();
});

// ---------------------------------------------------------------- staff

const staffDate = $("staff-date");
const staffAlert = $("staff-alert");
const appointmentList = $("appointment-list");
const listEmpty = $("list-empty");

let staffRequest = 0; // ignore stale responses when the date changes quickly

function showStaffError(message) {
  $("staff-alert-text").textContent = message;
  staffAlert.hidden = false;
}

async function loadStaff() {
  const date = staffDate.value;
  const requestId = ++staffRequest;
  staffAlert.hidden = true;
  listEmpty.hidden = true;
  appointmentList.setAttribute("aria-busy", "true");
  renderListSkeleton(appointmentList);

  try {
    // Independent requests, so fetch them at the same time.
    const [appointments, summary] = await Promise.all([getAppointments(date), getSummary(date)]);
    if (requestId !== staffRequest) return;
    renderSummary(summary);
    renderAppointments(appointmentList, appointments, markStatus);
    if (appointments.length === 0) {
      listEmpty.textContent = isSunday(date)
        ? "The health center is closed on Sundays."
        : `No appointments for ${formatDate(date)}.`;
      listEmpty.hidden = false;
    }
  } catch (error) {
    if (requestId !== staffRequest) return;
    appointmentList.replaceChildren();
    showStaffError(error.message);
  } finally {
    if (requestId === staffRequest) appointmentList.setAttribute("aria-busy", "false");
  }
}

async function markStatus(appointment, status, buttons) {
  buttons.forEach((b) => { b.disabled = true; });
  try {
    await updateStatus(appointment.id, status);
    await loadStaff(); // re-read list AND summary from the server, the source of truth
    // The clicked button no longer exists; keep keyboard focus somewhere sensible.
    $("list-heading").focus();
  } catch (error) {
    // 400/404 mean the server's data differs from what's on screen (e.g. another
    // staff member already marked it), so reload first, then show why it failed.
    await loadStaff();
    showStaffError(error.message);
  }
}

staffDate.addEventListener("change", () => { if (staffDate.value) loadStaff(); });
$("staff-retry").addEventListener("click", loadStaff);

// ---------------------------------------------------------------- start

dateInput.min = todayISO();
staffDate.value = todayISO();
selectTab(tabs[0]);
