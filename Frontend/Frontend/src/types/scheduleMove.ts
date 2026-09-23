// types/scheduleMove.ts

export interface MoveRequest {
  new_start_time: string;   // ISO 8601
  new_end_time:   string;
  admin_note?:    string;
}

export interface MoveHistoryEntry {
  from_start:  string;
  from_end:    string;
  to_start:    string;
  to_end:      string;
  admin_note?: string;
  moved_at:    string;
}

/** ← FIXED: matches PlanningRouter.py apply_move() actual return shape.
 *  The previous version declared from_start/from_end/to_start/to_end/
 *  move_count/message, none of which the backend actually returns. */
export interface MoveResponse {
  success:         boolean;
  slot_id:         number;
  session_number:  number;
  new_start_time:  string;   // ISO 8601
  new_end_time:    string;   // ISO 8601
}

/** Represents the target cell where a session is dropped. */
export interface DropTarget {
  day:        string;    // "Monday"
  week:       number;    // 1
  time_slot:  string;    // "08:00 → 11:00"
  start_time: string;    // ISO 8601
  end_time:   string;    // ISO 8601
}

/** Pending move state — BEFORE admin confirms. */
export interface PendingMove {
  slot_id:       number;
  course_title:  string;
  old_start:     string;
  old_end:       string;
  target:        DropTarget;
}