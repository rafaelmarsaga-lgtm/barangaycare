// DOM helpers. User-supplied text is always set with textContent, never
// innerHTML, so a name like "<script>" is shown as text instead of run (XSS).

export function formatSlot(slot) {
  const [hour, minute] = slot.split(":").map(Number);
  const suffix = hour < 12 ? "AM" : "PM";
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${hour12}:${String(minute).padStart(2, "0")} ${suffix}`;
}

export function formatDate(isoDate) {
  // Build the date from its parts so the browser's time zone can't shift the day.
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-PH", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
}

export function showFieldError(fieldName, message) {
  const input = document.getElementById(fieldName);
  const error = document.getElementById(`${fieldName}-error`);
  error.textContent = message;
  error.hidden = false;
  if (input) {
    input.setAttribute("aria-invalid", "true");
    input.classList.add("border-red-600");
  }
}

export function clearFieldErrors(form) {
  form.querySelectorAll(".field-error").forEach((el) => { el.hidden = true; el.textContent = ""; });
  form.querySelectorAll("[aria-invalid]").forEach((el) => {
    el.removeAttribute("aria-invalid");
    el.classList.remove("border-red-600");
  });
}

export function showAlert(element, message) {
  element.textContent = message;
  element.hidden = false;
}

export function hideAlert(element) {
  element.hidden = true;
  element.textContent = "";
}

export function setButtonLoading(button, spinner, label, loading, text) {
  button.disabled = loading;
  spinner.hidden = !loading;
  label.textContent = text;
}

export function renderSlotSkeleton(container) {
  container.replaceChildren();
  for (let i = 0; i < 7; i++) {
    const block = document.createElement("div");
    block.className = "h-[52px] animate-pulse rounded-lg bg-slate-200 motion-reduce:animate-none";
    container.append(block);
  }
}

/** Renders slots as a radio group; unavailable slots are disabled, not hidden,
 *  so residents can see the whole day at a glance. */
export function renderSlots(container, slots) {
  container.replaceChildren();
  for (const slot of slots) {
    const label = document.createElement("label");
    label.className = slot.available
      ? "flex min-h-[52px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-slate-300 bg-white px-2 py-1.5 text-center transition-colors hover:border-brand-600 has-[:checked]:border-brand-700 has-[:checked]:bg-brand-700 has-[:checked]:text-white has-[:focus-visible]:ring-4 has-[:focus-visible]:ring-brand-600/40 motion-reduce:transition-none"
      : "flex min-h-[52px] cursor-not-allowed flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 px-2 py-1.5 text-center text-slate-400";

    const input = document.createElement("input");
    input.type = "radio";
    input.name = "time_slot";
    input.value = slot.time;
    input.disabled = !slot.available;
    input.className = "sr-only";

    const time = document.createElement("span");
    time.className = "font-bold";
    time.textContent = formatSlot(slot.time);

    const note = document.createElement("span");
    note.className = "text-xs";
    note.textContent = slot.available ? "Open" : "Unavailable";

    label.append(input, time, note);
    container.append(label);
  }
}
