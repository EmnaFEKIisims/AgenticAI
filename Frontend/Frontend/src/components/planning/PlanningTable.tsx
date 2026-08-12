import type { SessionSlot } from "../../types/planning";
import Badge from "../ui/Badge";
import Card from "../ui/Card";
import Table, { type TableColumn } from "../ui/Table";
import { normalizeDayLabel } from "../../utils/planningHelpers";
import { getColorForCourse } from "../../utils/colorPalette";

interface PlanningTableProps {
  schedule: SessionSlot[];
  mode?: "global" | "group" | "trainer";
  showReasoning?: boolean;
}

const COLUMNS: Array<TableColumn<SessionSlot>> = [
  { key: "session_number", label: "#" },
  { key: "course_title", label: "Course" },
  { key: "trainer_name", label: "Trainer" },
  { key: "room_name", label: "Room" },
  { key: "group_name", label: "Group" },
  { key: "suggested_day", label: "Day" },
  { key: "suggested_time", label: "Time" },
  { key: "reasoning", label: "Reasoning" },
];

const DAYS_ORDER = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

function getDayRank(day: string): number {
  const normalized = day.trim().toLowerCase();
  const idx = DAYS_ORDER.indexOf(normalized);
  return idx === -1 ? Number.MAX_SAFE_INTEGER : idx;
}

function getTimeRank(timeRange: string): number {
  const [start = "99:99"] = timeRange.split("-");
  const [hour = "99", minute = "99"] = start.split(":");
  return Number(hour) * 60 + Number(minute);
}

export default function PlanningTable({ schedule, mode = "global", showReasoning = false }: PlanningTableProps) {
  if (!schedule.length) return null;

  // Filter columns based on showReasoning
  const displayColumns = COLUMNS.filter(
    (col) => col.key !== "reasoning" || showReasoning
  );

  if (mode !== "global") {
    const uniqueDays = Array.from(new Set(schedule.map((slot) => normalizeDayLabel(slot.suggested_day)))).sort(
      (a, b) => {
        const rankA = getDayRank(a);
        const rankB = getDayRank(b);
        if (rankA !== rankB) return rankA - rankB;
        return a.localeCompare(b);
      }
    );

    const uniqueTimes = Array.from(new Set(schedule.map((slot) => slot.suggested_time))).sort(
      (a, b) => getTimeRank(a) - getTimeRank(b)
    );

    const sessionsByCell = schedule.reduce<Record<string, SessionSlot[]>>((acc, slot) => {
      const key = `${normalizeDayLabel(slot.suggested_day)}__${slot.suggested_time}`;
      if (!acc[key]) acc[key] = [];
      acc[key].push(slot);
      return acc;
    }, {});

    return (
      <Card className="planning-table-wrapper planning-grid-wrapper">
        <table className="planning-grid-table">
          <thead>
            <tr>
              <th className="planning-th planning-grid-corner">Day / Time</th>
              {uniqueTimes.map((time) => (
                <th key={time} className="planning-th planning-grid-time-head">
                  {time}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {uniqueDays.map((day) => (
              <tr key={day} className="planning-row-even">
                <td className="planning-td planning-grid-day-cell">
                  <Badge className="planning-day-badge">{day}</Badge>
                </td>

                {uniqueTimes.map((time) => {
                  const key = `${day}__${time}`;
                  const sessions = sessionsByCell[key] ?? [];

                  return (
                    <td key={key} className="planning-td planning-grid-slot-cell">
                      {sessions.length === 0 ? (
                        <span className="planning-grid-empty">-</span>
                      ) : (
                        <div className="space-y-2">
                          {sessions.map((session) => {
                            const courseColor = getColorForCourse(session.course_title);
                            return (
                              <div 
                                key={session.session_number} 
                                className="planning-grid-session rounded-lg p-3 text-white shadow-md"
                                style={{ backgroundColor: courseColor }}
                              >
                                <p className="planning-grid-primary font-bold text-sm">{session.course_title}</p>
                                <p className="planning-grid-secondary opacity-90 text-xs">
                                  {mode === "group" ? session.trainer_name : session.group_name}
                                </p>
                                <p className="planning-grid-tertiary opacity-75 text-xs">Class: {session.room_name}</p>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    );
  }

  return (
    <Card className="planning-table-wrapper">
      <Table
        columns={displayColumns}
        rows={schedule}
        tableClassName="planning-table"
        thClassName="planning-th"
        tdClassName="planning-td"
        getRowKey={(row) => row.session_number}
        getRowClassName={(_, index) =>
          index % 2 === 0 ? "planning-row-even" : "planning-row-odd"
        }
        renderCell={(row, column) => {
          if (column.key === "session_number") {
            return <Badge className="planning-session-badge">#{row.session_number}</Badge>;
          }

          if (column.key === "course_title") {
            const courseColor = getColorForCourse(row.course_title);
            return (
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full shrink-0 shadow-sm"
                  style={{ backgroundColor: courseColor }}
                />
                <span className="font-medium text-gray-900">{row.course_title}</span>
              </div>
            );
          }

          if (column.key === "suggested_day") {
            return <Badge className="planning-day-badge">{normalizeDayLabel(row.suggested_day)}</Badge>;
          }

          if (column.key === "reasoning") {
            return <span className="planning-reasoning">{row.reasoning}</span>;
          }

          return String(row[column.key]);
        }}
      />
    </Card>
  );
}
