import { SessionSlot } from "../../types/planning";
import { normalizeDayLabel } from "../../utils/planningHelpers";
import { getColorForCourse, getColorWithOpacity } from "../../utils/colorPalette";
import { Clock, MapPin, Users } from "lucide-react";

interface CalendarGridViewProps {
  sessionsByDay: Record<string, SessionSlot[]>;
}

/**
 * Get text color (white or dark) based on background brightness
 */
function isColorLight(hexColor: string): boolean {
  const rgb = hexColor.match(/\d+/g);
  if (!rgb || rgb.length < 3) return false;
  const luminance = (0.299 * parseInt(rgb[0], 10) + 0.587 * parseInt(rgb[1], 10) + 0.114 * parseInt(rgb[2], 10)) / 255;
  return luminance > 0.5;
}

function parseTime(timeStr: string | undefined): number {
  // "08:00-11:00" -> 8
  if (!timeStr || typeof timeStr !== "string") return 8; // Default fallback
  const parts = timeStr.split("-");
  const [hours] = parts[0].split(":");
  const parsed = parseInt(hours, 10);
  return isNaN(parsed) ? 8 : parsed;
}

function parseTimeRange(timeStr: string | undefined): { start: number; duration: number } {
  // "08:00-11:00" -> { start: 8, duration: 3 }
  if (!timeStr || typeof timeStr !== "string") {
    return { start: 8, duration: 1 }; // Default fallback
  }

  const [startPart, endPart] = timeStr.split("-");
  if (!startPart || !endPart) {
    return { start: 8, duration: 1 }; // Fallback if malformed
  }

  const [startHours, startMins] = startPart.split(":").map(Number);
  const [endHours, endMins] = endPart.split(":").map(Number);

  const start = startHours + startMins / 60;
  const end = endHours + endMins / 60;
  const duration = end - start;

  return { start: isNaN(start) ? 8 : start, duration: isNaN(duration) ? 1 : duration };
}

export default function CalendarGridView({
  sessionsByDay,
}: CalendarGridViewProps) {
  if (Object.keys(sessionsByDay).length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No schedule data to display
      </div>
    );
  }

  // Extract days in order
  const dayOrder = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];
  const normalizedSessionsByDay = Object.entries(sessionsByDay).reduce<Record<string, SessionSlot[]>>(
    (acc, [day, sessions]) => {
      const normalizedDay = normalizeDayLabel(day);
      if (!acc[normalizedDay]) acc[normalizedDay] = [];
      acc[normalizedDay].push(...sessions);
      return acc;
    },
    {}
  );

  const days = dayOrder.filter((day) => normalizedSessionsByDay[day]);

  // Find time range across all sessions
  let minHour = 24;
  let maxHour = 0;

  Object.values(normalizedSessionsByDay).forEach((slots) => {
    slots.forEach((slot) => {
      if (!slot.suggested_time) return; // Skip sessions without time data
      const { start, duration } = parseTimeRange(slot.suggested_time);
      minHour = Math.min(minHour, Math.floor(start));
      maxHour = Math.max(maxHour, Math.ceil(start + duration));
    });
  });

  // Fallback if no valid time data found
  if (minHour === 24 || maxHour === 0) {
    minHour = 8;
    maxHour = 18;
  }

  // Generate time slots
  const timeSlots = Array.from(
    { length: maxHour - minHour },
    (_, i) => minHour + i
  );

  // Helper to position sessions in grid
  const getSessionStyle = (slot: SessionSlot) => {
    const { start, duration } = parseTimeRange(slot.suggested_time);
    const pixelsPerHour = 60;
    const topOffset = (start - minHour) * pixelsPerHour;
    const heightValue = duration * pixelsPerHour;

    return {
      top: `${topOffset}px`,
      height: `${heightValue}px`,
    };
  };

  // Get all unique courses for session coloring
  const courseColorMap = new Map<string, string>();
  Object.values(normalizedSessionsByDay)
    .flat()
    .filter((slot) => slot.suggested_time)
    .forEach((slot) => {
      if (!courseColorMap.has(slot.course_title)) {
        courseColorMap.set(slot.course_title, getColorForCourse(slot.course_title));
      }
    });

  return (
    <div className="w-full space-y-6 pb-8">
      {/* Color Legend */}
      {courseColorMap.size > 0 && (
        <div className="px-4 py-4 bg-white rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-xs font-bold text-gray-700 mb-3 uppercase tracking-wide">Course Color Legend</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Array.from(courseColorMap.entries()).map(([course, color]) => (
              <div key={course} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full shadow-sm border border-gray-200"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs text-gray-700 font-medium truncate">{course}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Calendar Grid */}
      <div className="grid grid-cols-1 gap-4 p-6 bg-linear-to-br from-gray-50 to-gray-100 rounded-2xl border border-gray-200 shadow-lg overflow-x-auto">
        {/* Header - Days */}
        <div className="flex gap-4 mb-6">
          {/* Time label column */}
          <div className="w-24 shrink-0" />

          {/* Day headers */}
          <div className="flex gap-4">
            {days.map((day) => (
              <div
                key={day}
                className="flex-1 min-w-72 text-center bg-white rounded-xl p-4 border border-gray-300 shadow-md"
              >
                <div className="font-bold text-gray-900 text-base mb-1">
                  {day}
                </div>
                <div className="text-sm text-gray-500 font-medium">
                  {normalizedSessionsByDay[day].filter((s) => s.suggested_time).length} sessions
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Time grid */}
        <div className="flex gap-4 relative bg-white rounded-2xl p-6 border border-gray-200 shadow-lg overflow-x-auto">
          {/* Time labels column */}
          <div className="w-24 shrink-0 border-r-2 border-gray-300 pr-4">
            {timeSlots.map((hour) => (
              <div
                key={hour}
                style={{ height: "80px" }}
                className="text-sm font-bold text-gray-700 flex items-start py-2"
              >
                {String(hour).padStart(2, "0")}:00
              </div>
            ))}
          </div>

          {/* Days grid */}
          <div className="flex gap-4 pb-4">
            {days.map((day) => (
              <div
                key={day}
                className="flex-1 min-w-72 relative bg-linear-to-b from-gray-50 to-white rounded-2xl border-2 border-gray-200 overflow-hidden shadow-md"
              >
                {/* Background time grid lines */}
                {timeSlots.map((hour) => (
                  <div
                    key={`grid-${hour}`}
                    style={{ height: "80px" }}
                    className="border-b-2 border-gray-100 last:border-b-0"
                  />
                ))}

                {/* Sessions positioned absolutely */}
                {normalizedSessionsByDay[day]
                  .filter((slot) => slot.suggested_time)
                  .map((slot) => {
                    const courseColor = courseColorMap.get(slot.course_title) || "#3B82F6";
                    const style = getSessionStyle(slot);
                    const textColor = isColorLight(courseColor) ? "#000000" : "#FFFFFF";

                    return (
                      <div
                        key={`${day}-${slot.session_number}`}
                        className="absolute left-2 right-2 rounded-lg p-0 cursor-pointer transition-all hover:shadow-2xl hover:scale-105 hover:z-20"
                        style={{
                          ...style,
                          boxShadow: `0 4px 12px rgba(0, 0, 0, 0.15)`,
                        }}
                      >
                        <div
                          className="h-full rounded-lg p-4 text-white relative group flex flex-col justify-between"
                          style={{
                            backgroundColor: courseColor,
                            color: textColor,
                            boxShadow: `0 6px 16px rgba(0, 0, 0, 0.2)`,
                          }}
                        >
                          {/* Main content */}
                          <div>
                            <div className="text-sm font-bold leading-tight mb-2" style={{ color: textColor }}>
                              {slot.course_title}
                            </div>
                            <div className="text-xs leading-tight" style={{ color: textColor, opacity: 0.9 }}>
                              Session {slot.session_number}
                            </div>
                          </div>

                          {/* Time info at bottom */}
                          <div className="text-xs font-semibold mt-2 pt-2 border-t" style={{ borderColor: textColor, opacity: 0.8, color: textColor }}>
                            {slot.suggested_time}
                          </div>

                          {/* Tooltip on hover */}
                          <div className="absolute left-0 top-full mt-2 hidden group-hover:block z-50 bg-gray-900 text-white text-xs rounded-xl p-4 w-56 shadow-2xl border border-gray-700">
                            <div className="font-bold mb-3 text-base">{slot.course_title}</div>
                            <div className="space-y-2.5 text-gray-100">
                              <div className="flex items-center gap-2">
                                <Users className="w-4 h-4 shrink-0" />
                                <span className="text-sm">{slot.trainer_name}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <MapPin className="w-4 h-4 shrink-0" />
                                <span className="text-sm">
                                  {slot.room_name} ({slot.group_name})
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4 shrink-0" />
                                <span className="text-sm font-semibold">{slot.suggested_time}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
