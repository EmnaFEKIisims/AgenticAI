import { CalendarDays, User, MapPin, Sparkles } from "lucide-react";

export type AuditPlanningStatus = "passed" | "warning" | "failed";

export interface AuditPlanningItem {
  id: string | number;
  day: string;
  course: string;
  start?: string;
  end?: string;
  time?: string;
  trainer?: string;
  room?: string;
  status: AuditPlanningStatus;
  score?: number;
  insight?: string;
}

interface AuditPlanningViewProps {
  sessions: AuditPlanningItem[];
  dayOrder?: string[];
  selectedSessionId?: string | number | null;
  onSelectSession?: (session: AuditPlanningItem) => void;
}

const DEFAULT_DAY_ORDER = [
  "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
  "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche",
];

function statusClasses(status: AuditPlanningStatus): {
  dot: string;
  chip: string;
  label: string;
} {
  switch (status) {
    case "passed":
      return {
        dot: "bg-emerald-500",
        chip: "border-emerald-100 bg-emerald-50 text-emerald-700",
        label: "Conforme",
      };
    case "warning":
      return {
        dot: "bg-amber-500",
        chip: "border-amber-100 bg-amber-50 text-amber-700",
        label: "Warning",
      };
    default:
      return {
        dot: "bg-rose-500",
        chip: "border-rose-100 bg-rose-50 text-rose-700",
        label: "Échec",
      };
  }
}

function parseTimeRange(session: AuditPlanningItem): { start: string; end: string } {
  if (session.start && session.end) return { start: session.start, end: session.end };
  if (session.time && session.time.includes("-")) {
    const [start, end] = session.time.split("-").map((v) => v.trim());
    return { start: start || "--:--", end: end || "--:--" };
  }
  return { start: "--:--", end: "--:--" };
}

function sortByStartTime(a: AuditPlanningItem, b: AuditPlanningItem): number {
  return parseTimeRange(a).start.localeCompare(parseTimeRange(b).start);
}

function getSessionKey(day: string, session: AuditPlanningItem, index: number): string {
  const { start, end } = parseTimeRange(session);
  return [day, session.course, start, end, session.id ?? index]
    .map((p) => String(p))
    .join("-");
}

export default function AuditPlanningView({
  sessions,
  dayOrder = DEFAULT_DAY_ORDER,
  selectedSessionId,
  onSelectSession,
}: AuditPlanningViewProps) {
  const grouped = sessions.reduce<Record<string, AuditPlanningItem[]>>((acc, session) => {
    if (!acc[session.day]) acc[session.day] = [];
    acc[session.day].push(session);
    return acc;
  }, {});

  const orderedDays = Object.keys(grouped).sort((a, b) => {
    const dayA = dayOrder.indexOf(a);
    const dayB = dayOrder.indexOf(b);
    if (dayA === -1 && dayB === -1) return a.localeCompare(b);
    if (dayA === -1) return 1;
    if (dayB === -1) return -1;
    return dayA - dayB;
  });

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <header className="flex items-start gap-4 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-5 sm:px-8">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
          <CalendarDays className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h3 className="text-base font-semibold tracking-tight text-slate-900">
            Audit planning view
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            Pedagogical reading of the schedule, grouped by day.
          </p>
        </div>
      </header>

      {sessions.length === 0 ? (
        <div className="px-6 py-16 text-center text-sm text-slate-500">
          Aucun slot de planning à afficher.
        </div>
      ) : (
        <div className="grid gap-5 bg-slate-50/40 p-6 sm:p-8 md:grid-cols-2 xl:grid-cols-3">
          {orderedDays.map((day) => {
            const daySessions = [...grouped[day]].sort(sortByStartTime);
            const dayLabel = day === "undefined" ? "Sessions sans jour" : day;

            return (
              <article
                key={day}
                className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
              >
                <header className="mb-3 flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                    {dayLabel}
                  </h4>
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                    {daySessions.length}
                  </span>
                </header>

                <div className="space-y-2.5">
                  {daySessions.map((session, index) => {
                    const status = statusClasses(session.status);
                    const time = parseTimeRange(session);
                    const isSelected = selectedSessionId === session.id;

                    return (
                      <button
                        type="button"
                        key={getSessionKey(day, session, index)}
                        onClick={() => onSelectSession?.(session)}
                        className={`w-full rounded-2xl border bg-white p-3.5 text-left transition ${
                          isSelected
                            ? "border-sky-200 bg-sky-50/30 ring-2 ring-sky-100"
                            : "border-slate-100 hover:border-slate-200 hover:shadow-sm"
                        } ${onSelectSession ? "active:scale-[0.99]" : ""}`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <p className="font-mono text-[11px] font-medium text-slate-500">
                              {time.start} – {time.end}
                            </p>
                            <p className="mt-0.5 truncate text-sm font-semibold text-slate-900">
                              {session.course}
                            </p>
                          </div>

                          <span
                            className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${status.chip}`}
                          >
                            <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
                            {status.label}
                          </span>
                        </div>

                        {(session.trainer || session.room) && (
                          <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                            {session.trainer && (
                              <span className="inline-flex items-center gap-1">
                                <User className="h-3 w-3" aria-hidden="true" />
                                {session.trainer}
                              </span>
                            )}
                            {session.room && (
                              <span className="inline-flex items-center gap-1">
                                <MapPin className="h-3 w-3" aria-hidden="true" />
                                {session.room}
                              </span>
                            )}
                          </div>
                        )}

                        {typeof session.score === "number" && (
                          <div className="mt-2 flex items-center gap-2">
                            <div className="h-1 flex-1 overflow-hidden rounded-full bg-slate-100">
                              <div
                                className={`h-full rounded-full ${
                                  session.status === "passed"
                                    ? "bg-emerald-500"
                                    : session.status === "warning"
                                    ? "bg-amber-500"
                                    : "bg-rose-500"
                                }`}
                                style={{ width: `${Math.min(100, Math.max(0, session.score))}%` }}
                              />
                            </div>
                            <span className="font-mono text-[10px] font-semibold text-slate-500">
                              {session.score.toFixed(0)}/100
                            </span>
                          </div>
                        )}

                        {session.insight && (
                          <div className="mt-2.5 flex items-start gap-2 rounded-xl border border-slate-100 bg-slate-50/60 p-2.5">
                            <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-slate-400" aria-hidden="true" />
                            <p className="text-[11px] leading-relaxed text-slate-600">
                              {session.insight}
                            </p>
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}