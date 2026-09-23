// Talks to the FastAPI backend. Every error the server sends has the shape
// {"detail": "<friendly message>"}, so callers can show error.message as-is.

const OFFLINE_MESSAGE = "Cannot reach the server. Please check your connection and try again.";
const GENERIC_MESSAGE = "Something went wrong. Please try again.";

export async function getSlots(date) {
  let response;
  try {
    response = await fetch(`/api/slots?date=${encodeURIComponent(date)}`);
  } catch {
    throw new Error(OFFLINE_MESSAGE);
  }
  // A crash (500) may return plain text, not JSON; don't let that leak to the UI.
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || GENERIC_MESSAGE);
  return data;
}

export async function createAppointment(appointment) {
  let response;
  try {
    response = await fetch("/api/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(appointment),
    });
  } catch {
    throw new Error(OFFLINE_MESSAGE);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || GENERIC_MESSAGE);
    error.status = response.status; // app.js reloads slots on 409
    throw error;
  }
  return data;
}
