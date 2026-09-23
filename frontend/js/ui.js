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

const STATUS_BADGE = {
  Booked: "bg-brand-100 text-brand-900",
  Completed: "bg-green-100 text-green-800",
  "No-show": "bg-amber-100 text-amber-900",
};

function textEl(tag, className, text) {
  const el = document.createElement(tag);
  el.className = className;
  el.textContent = text;
  return el;
}

export function renderSummary(summary) {
  document.getElementById("sum-total").textContent = summary.total;
  document.getElementById("sum-open").textContent = summary.open_slots;
  document.querySelectorAll("[data-service]").forEach((dd) => {
    dd.textContent = summary.by_service[dd.dataset.service] ?? 0;
  });
}

export function renderListSkeleton(list) {
  list.replaceChildren();
  for (let i = 0; i < 3; i++) {
    const row = document.createElement("li");
    row.className = "border-b border-brand-100 px-5 py-4 last:border-0";
    row.append(textEl("div", "h-6 animate-pulse rounded bg-slate-200 motion-reduce:animate-none", ""));
    list.append(row);
  }
}

/** One row per appointment. `onMark(appointment, status, buttons)` is called
 *  when staff click Completed / No-show; buttons only exist while Booked,
 *  because Completed and No-show are final. */
export function renderAppointments(list, appointments, onMark) {
  list.replaceChildren();
  for (const appt of appointments) {
    const row = document.createElement("li");
    // minmax(0,1fr), not 1fr: a plain 1fr column can't shrink below its longest
    // word, so one long unbroken name would push the page sideways on phones.
    row.className = "grid grid-cols-[6rem_minmax(0,1fr)] items-center gap-x-4 gap-y-2 border-b border-brand-100 px-5 py-4 last:border-0 md:grid-cols-[6rem_minmax(0,1fr)_9rem_8rem_13rem] md:gap-y-0";

    const time = textEl("span", "row-span-3 self-start whitespace-nowrap text-lg font-bold text-brand-900 md:row-span-1 md:self-center", formatSlot(appt.time_slot));

    const who = document.createElement("div");
    who.append(
      textEl("p", "font-bold text-slate-900 [overflow-wrap:anywhere]", appt.name),
      textEl("p", "text-sm text-slate-600", appt.contact_number),
    );

    const service = textEl("span", "text-slate-700", appt.service);

    const badge = textEl("span", `w-fit rounded-full px-3 py-1 text-sm font-bold ${STATUS_BADGE[appt.status] || ""}`, appt.status);

    const actions = document.createElement("div");
    actions.className = "col-span-2 flex gap-2 md:col-span-1 md:justify-end";
    if (appt.status === "Booked") {
      const done = textEl("button", "min-h-[44px] flex-1 cursor-pointer rounded-lg bg-green-700 px-3 text-sm font-bold text-white hover:bg-green-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-green-600/40 disabled:cursor-wait disabled:opacity-60 md:flex-none", "Completed");
      const noShow = textEl("button", "min-h-[44px] flex-1 cursor-pointer rounded-lg border-2 border-amber-700 px-3 text-sm font-bold text-amber-900 hover:bg-amber-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-amber-600/40 disabled:cursor-wait disabled:opacity-60 md:flex-none", "No-show");
      for (const button of [done, noShow]) {
        button.type = "button";
        // Screen readers hear "Completed, Juan Dela Cruz 9:00 AM" instead of just "Completed".
        button.setAttribute("aria-label", `Mark ${appt.name} (${formatSlot(appt.time_slot)}) as ${button.textContent}`);
        button.addEventListener("click", () => onMark(appt, button.textContent, [done, noShow]));
      }
      actions.append(done, noShow);
    }

    // Phones: time on the left, details stacked on the right, buttons full width below.
    const details = document.createElement("div");
    details.className = "contents";
    details.append(who, service, badge);
    row.append(time, details, actions);
    list.append(row);
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
