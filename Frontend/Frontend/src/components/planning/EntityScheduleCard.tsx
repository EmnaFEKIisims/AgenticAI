import type { SessionSlot } from "../../types/planning";

interface EntityScheduleCardProps {
  title: string;
  sessions: SessionSlot[];
  entityType: "Group" | "Trainer";
  timeSlots: string[];
}

interface DisplaySession {
  session: SessionSlot;
  occurrenceCount: number;
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const DAY_ABBREVIATIONS = ["Mon", "Tue", "Wed", "Thu", "Fri"];

const COLORS = [
  "bg-sky-50 border-sky-200 text-sky-900",
  "bg-violet-50 border-violet-200 text-violet-900",
  "bg-emerald-50 border-emerald-200 text-emerald-900",
  "bg-amber-50 border-amber-200 text-amber-900",
  "bg-rose-50 border-rose-200 text-rose-900",
  "bg-indigo-50 border-indigo-200 text-indigo-900",
];

function colorFor(title: string): string {
  let hash = 0;
  for (const character of title) hash = (hash * 31 + character.charCodeAt(0)) & 0xffff;
  return COLORS[hash % COLORS.length];
}

function dayName(value: string): string {
  return value.replace(/^Week\s+\d+\s*[—-]?\s*/i, "").trim();
}

export default function EntityScheduleCard({ title, sessions, entityType, timeSlots }: EntityScheduleCardProps) {
  const groupedSessions = new Map<string, DisplaySession>();

  sessions.forEach((session) => {
    const secondaryName = entityType === "Trainer" ? session.group_name : session.trainer_name;
    const key = [session.course_title, secondaryName, session.room_name].join("|");
    const existing = groupedSessions.get(key);

    if (existing) {
      existing.occurrenceCount += 1;
      return;
    }

    groupedSessions.set(key, {
      session,
      occurrenceCount: 1,
    });
  });

  const displaySessions = Array.from(groupedSessions.values());
  const cells = new Map<string, DisplaySession[]>();

  displaySessions.forEach((displaySession) => {
    const key = `${dayName(displaySession.session.suggested_day)}|${displaySession.session.suggested_time}`;
    const cell = cells.get(key) ?? [];
    cell.push(displaySession);
    cells.set(key, cell);
  });

  return (
    <article
      className="planning-entity-card overflow-hidden rounded-2xl bg-white p-0"
      style={{
        border: "2px solid #94a3b8",
        boxShadow: "0 4px 14px rgba(15, 23, 42, 0.12)",
      }}
    >
      <div className="flex items-center justify-between gap-4 border-b border-slate-100 bg-slate-50 px-5 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-xs font-bold text-white shadow-sm">
            {title.trim().slice(0, 2).toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">{entityType}</p>
            <h3 className="mt-0.5 truncate text-base font-bold tracking-tight text-slate-900">{title}</h3>
          </div>
        </div>
        <span className="shrink-0 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">
          {displaySessions.length} sessions
        </span>
        </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-180 text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="w-28 px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Day</th>
              {timeSlots.map((time) => (
                <th key={time} className="min-w-52 px-2 py-3 text-center text-xs font-semibold text-slate-500">{time}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {DAYS.map((day, index) => (
              <tr key={day}>
                <td className="px-4 py-3 text-xs font-semibold text-slate-700">
                  <div>{day}</div>
                  <div className="text-slate-400">{DAY_ABBREVIATIONS[index]}</div>
                </td>
                {timeSlots.map((time) => {
                  const cellSessions = cells.get(`${day}|${time}`) ?? [];
                  return (
                    <td key={time} className="px-2 py-2 align-top">
                      <div className="space-y-2">
                        {cellSessions.map(({ session, occurrenceCount }) => (
                          <div key={session.id ?? session.session_number} className={`relative rounded-xl border p-2.5 ${colorFor(session.course_title)}`}>
                            <p className="pr-8 font-semibold text-xs leading-snug">{session.course_title}</p>
                            <p className="mt-1 text-xs opacity-70 truncate">
                              {entityType === "Trainer" ? session.group_name : session.trainer_name}
                            </p>
                            <p className="text-xs opacity-60 truncate">{session.room_name}</p>
                            {occurrenceCount > 1 && (
                              <span className="absolute bottom-2 right-2 rounded-full bg-white/70 px-2 py-0.5 text-[10px] font-bold shadow-sm">
                                x{occurrenceCount}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}