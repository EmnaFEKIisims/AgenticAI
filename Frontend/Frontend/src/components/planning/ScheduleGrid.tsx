// components/planning/ScheduleGrid.tsx
// Weekly timetable with drag & drop support.
// Each session card = DraggableScheduleSlot
// Each empty cell  = DropZone
//
// ← FIXED: toISO() used a hardcoded referenceMonday = "2025-09-01" fallback.
//   Every drop-target date was computed from that fake anchor instead of the
//   planning's real start date, so a session generated in week X of 2026
//   would compute a drop target a full YEAR off (confirmed against the
//   PATCH /planning/session/211/move log: dragging to "week 0, Friday"
//   from the hardcoded 2025-09-01 anchor produces exactly "2025-09-05",
//   which is what was actually saved). Now the reference Monday is derived
//   from a real session's actual start_time in the current schedule.

import { useState, useMemo } from "react";
import type { SessionSlotOut } from "../../types/planningRegeneration";
import type { PendingMove }    from "../../types/scheduleMove";
import DraggableScheduleSlot from "./DraggableScheduleSlot";
import DropZone from "./DropZone";

const DAYS     = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const DAYS_ABR = ["Mon",    "Tue",     "Wed",       "Thu",      "Fri"];

function extractWeek(suggestedDay: string): number {
  return parseInt(suggestedDay?.match(/Week\s+(\d+)/i)?.[1] ?? "1");
}
function extractDay(suggestedDay: string): string {
  return suggestedDay?.split("—")[1]?.trim() ?? suggestedDay;
}

/** Zero-pad a date component. */
function pad(n: number): string {
  return String(n).padStart(2, "0");
}

/**
 * ← ADDED: derive the real "Week 1 Monday" from a session that already has
 * a genuine ISO start_time, instead of trusting a hardcoded date. Works
 * back from that session's (week, day) label to what Week 1 Monday must
 * have been.
 */
function deriveReferenceMonday(sessions: SessionSlotOut[]): Date | null {
  for (const s of sessions) {
    if (!s.start_time) continue;
    const start = new Date(s.start_time);
    if (isNaN(start.getTime())) continue;

    const week   = extractWeek(s.suggested_day) - 1;
    const dayIdx = DAYS.indexOf(extractDay(s.suggested_day));
    if (dayIdx === -1) continue;

    const monday = new Date(start);
    monday.setDate(monday.getDate() - (week * 7 + dayIdx));
    monday.setHours(0, 0, 0, 0);
    return monday;
  }
  return null;
}

// Converts "Week 1 — Monday" + "08:00 → 11:00" → ISO start/end datetime,
// anchored on the schedule's REAL reference Monday (not a hardcoded date).
// ← FIXED: also stopped using toISOString().slice(0, 10) to build the date
//   part — that converts to UTC first, which can silently shift the date
//   by one day for timezones ahead of UTC (e.g. UTC+1). Now built from
//   local date components instead.
function toISO(suggestedDay: string, timeSlot: string, referenceMonday: Date): [string, string] {
  const week    = extractWeek(suggestedDay) - 1;
  const dayIdx  = DAYS.indexOf(extractDay(suggestedDay));
  const [s, e]  = timeSlot.split("→").map(t => t.trim());

  const base = new Date(referenceMonday);
  base.setDate(base.getDate() + week * 7 + dayIdx);

  const dateStr = `${base.getFullYear()}-${pad(base.getMonth() + 1)}-${pad(base.getDate())}`;
  const fmt = (t: string) => `${dateStr}T${t}:00`;
  return [fmt(s), fmt(e)];
}

interface ScheduleGridProps {
  sessions:        SessionSlotOut[];
  planningGroupId: string;
  currentWeek:     number;
  totalWeeks:      number;
  draggingSlotId:  number | null;
  onWeekChange:    (week: number) => void;
  onDragStart:     (e: React.DragEvent, session: SessionSlotOut) => void;
  onDragEnd:       () => void;
  onDrop:          (pendingMove: PendingMove) => void;
}

export default function ScheduleGrid({
  sessions, planningGroupId, currentWeek, totalWeeks,
  draggingSlotId, onWeekChange, onDragStart, onDragEnd, onDrop,
}: ScheduleGridProps) {

  const [overCell, setOverCell] = useState<string | null>(null);

  // ← ADDED: the real reference Monday for this schedule, derived from
  //   actual session data instead of a hardcoded fallback.
  const referenceMonday = useMemo(() => {
    return deriveReferenceMonday(sessions) ?? (() => {
      // Only reached if NO session in the schedule has a valid start_time
      // (shouldn't happen with the backend/type fixes already in place).
      // Falling back to "today" rather than a fixed stale date at least
      // keeps drops in the current year instead of silently jumping a
      // year back.
      const d = new Date();
      d.setHours(0, 0, 0, 0);
      d.setDate(d.getDate() - d.getDay() + 1); // this week's Monday
      return d;
    })();
  }, [sessions]);

  // Time slots and week sessions
  const allTimeSlots = useMemo(() =>
    Array.from(new Set(sessions.map(s => s.suggested_time))).sort(),
    [sessions]
  );
  const weekSessions = sessions.filter(s => extractWeek(s.suggested_day) === currentWeek);

  // Grid: "Day|TimeSlot" → session
  const grid = useMemo(() => {
    const m = new Map<string, SessionSlotOut>();
    weekSessions.forEach(s => m.set(`${extractDay(s.suggested_day)}|${s.suggested_time}`, s));
    return m;
  }, [weekSessions]);

  const handleDrop = (
    _e: React.DragEvent, day: string, week: number,
    timeSlot: string, start: string, end: string
  ) => {
    setOverCell(null);
    // Find the dragged session
    const dragged = sessions.find(s => (s.id ?? s.session_number) === draggingSlotId);
    if (!dragged) return;
    if (extractDay(dragged.suggested_day) === day && dragged.suggested_time === timeSlot) return;

    onDrop({
      slot_id:      dragged.id ?? dragged.session_number,
      course_title: dragged.course_title,
      old_start:    start,
      old_end:      end,
      target:       { day, week, time_slot: timeSlot, start_time: start, end_time: end },
    });
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">

      {/* Week navigator */}
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Schedule — drag to rearrange
          </p>
          <p className="text-sm text-slate-500 mt-0.5">{weekSessions.length} session(s) this week</p>
        </div>
        <div className="flex items-center gap-1 rounded-2xl border border-slate-200 bg-slate-50 p-1">
          <button onClick={() => onWeekChange(currentWeek - 1)} disabled={currentWeek <= 1}
            className="rounded-xl px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-white disabled:opacity-30">←</button>
          <span className="px-4 py-1 text-sm font-semibold text-slate-800">
            Week {currentWeek} <span className="text-xs font-normal text-slate-400">/ {totalWeeks}</span>
          </span>
          <button onClick={() => onWeekChange(currentWeek + 1)} disabled={currentWeek >= totalWeeks}
            className="rounded-xl px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-white disabled:opacity-30">→</button>
        </div>
      </div>

      {/* Timetable */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 w-24">Day</th>
              {allTimeSlots.map(slot => (
                <th key={slot} className="px-2 py-3 text-center text-xs font-semibold text-slate-500 min-w-44">
                  {slot}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {DAYS.map((day, di) => (
              <tr key={day}>
                <td className="px-4 py-3 text-xs font-semibold text-slate-700">
                  <div>{day}</div>
                  <div className="text-slate-400">{DAYS_ABR[di]}</div>
                </td>
                {allTimeSlots.map(slot => {
                  const session  = grid.get(`${day}|${slot}`);
                  const cellKey  = `${day}|${slot}`;
                  const isOver   = overCell === cellKey;
                  const [s, e]   = toISO(`Week ${currentWeek} — ${day}`, slot, referenceMonday);

                  return (
                    <td key={slot} className={`px-2 py-2 transition-colors ${isOver ? "bg-sky-50" : ""}`}>
                      {session ? (
                        <DraggableScheduleSlot
                          session     = {session}
                          isDragging  = {(session.id ?? session.session_number) === draggingSlotId}
                          onDragStart = {onDragStart}
                          onDragEnd   = {onDragEnd}
                        />
                      ) : (
                        <DropZone
                          day        = {day}
                          week       = {currentWeek}
                          timeSlot   = {slot}
                          startTime  = {s}
                          endTime    = {e}
                          isOver     = {isOver}
                          onDragOver = {() => setOverCell(cellKey)}
                          onDragLeave= {() => setOverCell(null)}
                          onDrop     = {handleDrop}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Week dots */}
      {totalWeeks > 1 && (
        <div className="flex justify-center gap-1.5 border-t border-slate-100 py-3">
          {Array.from({ length: totalWeeks }, (_, i) => i + 1).map(w => (
            <button key={w} onClick={() => onWeekChange(w)}
              className={`h-2 rounded-full transition-all ${
                w === currentWeek ? "w-6 bg-slate-800" : "w-2 bg-slate-300 hover:bg-slate-400"
              }`} />
          ))}
        </div>
      )}
    </div>
  );
}