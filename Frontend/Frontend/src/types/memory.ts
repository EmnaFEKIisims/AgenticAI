// src/types/memory.ts

export type { MemoryType } from "./rag";
import type { MemoryType } from "./rag";

export interface Memory {
  id:          string;
  content:     string;
  type:        MemoryType;
  importance:  number;    // 1=low 2=medium 3=high
  created_at:  string | null;
  planning_id: string | null;
  tags:        string[];
}

export interface MemorySummary {
  user_id:  string;
  total:    number;
  by_type:  Record<MemoryType, number>;
  recent:   Array<{ content: string; type: MemoryType; created_at: string }>;
}

export interface FeedbackRequest {
  user_id:      string;
  feedback:     string;
  context?:     string;
  planning_id?: string;
}