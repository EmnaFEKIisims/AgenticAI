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
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
  "Lundi",
  "Mardi",
  "Mercredi",
  "Jeudi",
  "Vendredi",
  "Samedi",
  "Dimanche",
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
        chip: "border-emerald-200 bg-emerald-50 text-emerald-700",
        label: "Conforme",
      };
    case "warning":
      return {
        dot: "bg-amber-500",
        chip: "border-amber-200 bg-amber-50 text-amber-700",
        label: "Warning",
      };
    default:
      return {
        dot: "bg-rose-500",
        chip: "border-rose-200 bg-rose-50 text-rose-700",
        label: "Echec",
      };
  }
}

function parseTimeRange(session: AuditPlanningItem): { start: string; end: string } {
  if (session.start && session.end) {
    return { start: session.start, end: session.end };
  }

  if (session.time && session.time.includes("-")) {
    const [start, end] = session.time.split("-").map((value) => value.trim());
    return { start: start || "--:--", end: end || "--:--" };
  }

  return { start: "--:--", end: "--:--" };
}

function sortByStartTime(a: AuditPlanningItem, b: AuditPlanningItem): number {
  const aTime = parseTimeRange(a).start;
  const bTime = parseTimeRange(b).start;
  return aTime.localeCompare(bTime);
}

export default function AuditPlanningView({
  sessions,
  dayOrder = DEFAULT_DAY_ORDER,
  selectedSessionId,
  onSelectSession,
}: AuditPlanningViewProps) {
  const grouped = sessions.reduce<Record<string, AuditPlanningItem[]>>((acc, session) => {
    if (!acc[session.day]) {
      acc[session.day] = [];
    }
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
      <div className="border-b border-slate-200 bg-linear-to-r from-slate-50 to-white px-6 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Audit Planning View
        </p>
        <h3 className="mt-1 text-lg font-bold text-slate-900">Lecture pedagogique du planning</h3>
      </div>

      {sessions.length === 0 ? (
        <div className="px-6 py-10 text-center text-sm text-slate-500">
          Aucun slot de planning a afficher.
        </div>
      ) : (
        <div className="grid gap-5 p-5 md:grid-cols-2 xl:grid-cols-3">
          {orderedDays.map((day) => {
            const daySessions = [...grouped[day]].sort(sortByStartTime);

            return (
              <article key={day} className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
                <h4 className="text-sm font-bold uppercase tracking-[0.12em] text-slate-700">{day}</h4>

                <div className="mt-3 space-y-3">
                  {daySessions.map((session) => {
                    const status = statusClasses(session.status);
                    const time = parseTimeRange(session);
                    const isSelected = selectedSessionId === session.id;

                    return (
                      <button
                        type="button"
                        key={session.id}
                        onClick={() => onSelectSession?.(session)}
                        className={`w-full rounded-2xl border bg-white p-3 text-left shadow-sm transition ${
                          isSelected
                            ? "border-sky-300 ring-2 ring-sky-100"
                            : "border-slate-200 hover:border-slate-300"
                        } ${onSelectSession ? "active:scale-[0.99]" : ""}`}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-xs font-medium text-slate-500">
                              {time.start} - {time.end}
                            </p>
                            <p className="mt-0.5 font-semibold text-slate-900">{session.course}</p>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className={`h-2.5 w-2.5 rounded-full ${status.dot}`} />
                            <span
                              className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${status.chip}`}
                            >
                              {status.label}
                            </span>
                          </div>
                        </div>

                        {(session.trainer || session.room) && (
                          <p className="mt-2 text-xs text-slate-500">
                            {session.trainer ? `Formateur: ${session.trainer}` : ""}
                            {session.trainer && session.room ? " • " : ""}
                            {session.room ? `Salle: ${session.room}` : ""}
                          </p>
                        )}

                        {typeof session.score === "number" && (
                          <p className="mt-1 text-xs font-medium text-slate-600">
                            Score pedagogique: {session.score.toFixed(0)}/100
                          </p>
                        )}

                        {session.insight && (
                          <p className="mt-2 rounded-xl bg-slate-50 p-2 text-xs leading-relaxed text-slate-600">
                            {session.insight}
                          </p>
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
