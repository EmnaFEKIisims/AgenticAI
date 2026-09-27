// components/planning/DraggableScheduleSlot.tsx
// Draggable session card inside the timetable grid.

import type { SessionSlotOut } from "../../types/planningRegeneration";

const COLORS = [
  "bg-sky-50    border-sky-200    text-sky-900",
  "bg-violet-50 border-violet-200 text-violet-900",
  "bg-emerald-50 border-emerald-200 text-emerald-900",
  "bg-amber-50   border-amber-200   text-amber-900",
  "bg-rose-50    border-rose-200    text-rose-900",
  "bg-indigo-50  border-indigo-200  text-indigo-900",
];
function pickColor(title: string) {
  let h = 0;
  for (const c of title) h = (h * 31 + c.charCodeAt(0)) & 0xffff;
  return COLORS[h % COLORS.length];
}

interface DraggableScheduleSlotProps {
  session:     SessionSlotOut;
  isDragging?:  boolean;
  onDragStart?: (e: React.DragEvent, session: SessionSlotOut) => void;
  onDragEnd?:   () => void;
}

export default function DraggableScheduleSlot({
  session, isDragging, onDragStart, onDragEnd,
}: DraggableScheduleSlotProps) {
  return (
    <div
      draggable={Boolean(onDragStart)}
      onDragStart={e => onDragStart?.(e, session)}
      onDragEnd={() => onDragEnd?.()}
      className={`cursor-grab active:cursor-grabbing select-none rounded-xl border p-2.5 transition-all ${pickColor(session.course_title)} ${
        isDragging ? "opacity-40 scale-95 shadow-none" : "hover:shadow-md hover:scale-[1.02]"
      }`}
    >
      <p className="font-semibold text-xs leading-snug line-clamp-2">
        {session.course_title}
      </p>
      <p className="mt-1 text-xs opacity-70 truncate">{session.trainer_name}</p>
      <p className="text-xs opacity-60 truncate">{session.room_name}</p>
      <p className="mt-1.5 text-xs opacity-40 flex items-center gap-1">
        <span>⠿</span> drag to move
      </p>
    </div>
  );
}
