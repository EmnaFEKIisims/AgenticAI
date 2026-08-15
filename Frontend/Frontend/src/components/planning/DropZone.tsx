// components/planning/DropZone.tsx
// Empty timetable cell — accepts dragged sessions.

interface DropZoneProps {
  day:       string;
  week:      number;
  timeSlot:  string;
  startTime: string;
  endTime:   string;
  isOver:    boolean;
  onDragOver:  (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop:      (e: React.DragEvent, day: string, week: number, timeSlot: string, start: string, end: string) => void;
}

export default function DropZone({
  day, week, timeSlot, startTime, endTime,
  isOver, onDragOver, onDragLeave, onDrop,
}: DropZoneProps) {
  return (
    <div
      onDragOver={e => { e.preventDefault(); onDragOver(e); }}
      onDragLeave={onDragLeave}
      onDrop={e => { e.preventDefault(); onDrop(e, day, week, timeSlot, startTime, endTime); }}
      className={`h-20 rounded-xl border-2 border-dashed transition-all ${
        isOver
          ? "border-sky-400 bg-sky-50 scale-[1.02]"
          : "border-slate-100 hover:border-slate-200"
      }`}
    >
      {isOver && (
        <div className="flex h-full items-center justify-center">
          <p className="text-xs font-semibold text-sky-600">Drop here</p>
        </div>
      )}
    </div>
  );
}