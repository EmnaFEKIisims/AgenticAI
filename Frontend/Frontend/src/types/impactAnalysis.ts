// types/impactAnalysis.ts

export interface ImpactRequest {
  new_start_time:     string;
  new_end_time:       string;
  planning_group_id?: string;
}

export interface ImpactConflict {
  conflict_type: string;    // "trainer" | "room" | "group" | "resolved"
  slot_id:       number;
  course_title:  string;
  trainer_name:  string;
  room_name:     string;
  group_name:    string;
  start_time:    string;
  end_time:      string;
  description:   string;
}

export interface AffectedSession {
  slot_id:      number;
  course_title: string;
  trainer_name: string;
  room_name:    string;
  start_time:   string;
  end_time:     string;
  relation:     string;   // "same_trainer" | "same_room" | "same_group"
}

export interface ImpactResponse {
  slot_id:            number;
  course_title:       string;
  proposed_start:     string;
  proposed_end:       string;
  is_safe:            boolean;
  new_conflicts:      ImpactConflict[];
  resolved_conflicts: ImpactConflict[];
  affected_sessions:  AffectedSession[];
  summary:            string;
  recommendation:     string;
}