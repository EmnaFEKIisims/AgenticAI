// src/types/rag.ts

export type MemoryType =
  | "user_preference"
  | "decision_history"
  | "planning_history"
  | "conflict_correction"
  | "user_feedback"
  | "pedagogical_knowledge";

export interface RAGContextResponse {
  user_id:      string;
  context:      string;
  has_context:  boolean;
  memory_count: number;
}

export interface KnowledgeDocument {
  id:           number;
  title:        string;
  source:       string | null;
  type:         string;
  is_indexed:   boolean;
  chunks:       number;
}

export interface PlanningValidatedEvent {
  user_id:     string;
  planning_id: string;
  notes?:      string;
  schedule?:   unknown[];
  constraints?: Record<string, unknown>;
}

export interface PlanningRejectedEvent {
  user_id:     string;
  planning_id: string;
  reason?:     string;
}

export interface SessionMovedEvent {
  user_id:      string;
  planning_id:  string;
  course_title: string;
  from_day:     string;
  to_day:       string;
  from_time:    string;
  to_time:      string;
  admin_note?:  string;
}