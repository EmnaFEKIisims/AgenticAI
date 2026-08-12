const DAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export function normalizeDayLabel(day: string): string {
  const value = String(day ?? "").trim();
  if (!value) return value;

  const lowerValue = value.toLowerCase();
  const matchedDay = DAY_NAMES.find((name) => lowerValue.includes(name.toLowerCase()));
  if (matchedDay) return matchedDay;

  const exactMatch = DAY_NAMES.find((name) => lowerValue === name.toLowerCase());
  if (exactMatch) return exactMatch;

  return value;
}