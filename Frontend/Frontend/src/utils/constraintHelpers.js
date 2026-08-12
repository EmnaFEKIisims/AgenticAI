/** Utility helpers to parse, merge and validate constraint inputs. */

export function parseLines(text) {
  if (!text) return [];
  return String(text)
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export function mergeConstraints(iso = [], pedagogicalText = "", userText = "") {
  const userLines = parseLines(userText);
  const weekdays = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"];
  const forbidden_days = userLines.filter((l) => weekdays.some((d) => l.toLowerCase().includes(d)));

  const pedagogical_rules = parseLines(pedagogicalText);

  return {
    forbidden_days,
    trainer_availability: [],
    planning_parameters: [],
    pedagogical_rules,
    iso: Array.isArray(iso) ? iso : [],
  };
}

export function validateConstraints(merged) {
  const issues = [];
  const warnings = [];

  const p = (merged.planning_parameters || []).find((x) => x.label && x.label.toLowerCase().includes("sessions"));
  if (p) {
    const val = Number(p.value || 0);
    if (!Number.isNaN(val) && val > 8) {
      issues.push({ code: "max_sessions_per_day", message: `${val} exceeds recommended maximum of 8`, suggestion: "Set sessions per day <= 8" });
    }
  }

  if (!merged.forbidden_days || merged.forbidden_days.length === 0) {
    warnings.push("No forbidden days set.");
  }

  if (!merged.trainer_availability || merged.trainer_availability.length === 0) {
    warnings.push("No trainer availability specified.");
  }

  const status = issues.length ? "invalid" : warnings.length ? "warning" : "valid";

  return { status, issues, warnings };
}
