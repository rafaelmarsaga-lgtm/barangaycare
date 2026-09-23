// Talks to the FastAPI backend. Every error the server sends has the shape
// {"detail": "<friendly message>"}, so callers can show error.message as-is.

const OFFLINE_MESSAGE = "Cannot reach the server. Please check your connection and try again.";
const GENERIC_MESSAGE = "Something went wrong. Please try again.";

/** One place for fetch + error handling. Resolves with the JSON body, or throws
 *  an Error whose message is safe to show and whose `status` is the HTTP code. */
async function request(method, path, body) {
  const options = { method };
  if (body !== undefined) {
    options.headers = { "Content-Type": "application/json" };
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error(OFFLINE_MESSAGE); // network down or server stopped
  }
  // A crash (500) may return plain text, not JSON; don't let that leak to the UI.
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || GENERIC_MESSAGE);
    error.status = response.status; // app.js reloads slots on 409
    throw error;
  }
  return data;
}

const byDate = (path, date) => `${path}?date=${encodeURIComponent(date)}`;

export const getSlots = (date) => request("GET", byDate("/api/slots", date));
export const getAppointments = (date) => request("GET", byDate("/api/appointments", date));
export const getSummary = (date) => request("GET", byDate("/api/summary", date));
export const createAppointment = (appointment) => request("POST", "/api/appointments", appointment);
export const updateStatus = (id, status) =>
  request("PATCH", `/api/appointments/${encodeURIComponent(id)}/status`, { status });
