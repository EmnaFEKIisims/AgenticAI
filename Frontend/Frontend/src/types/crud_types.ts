// src/types/room.ts
export interface Room { id: number; name: string; room_type: string; capacity: number; is_active: boolean; }
export interface RoomCreate { name: string; room_type: string; capacity: number; }
export interface RoomUpdate { name?: string; room_type?: string; capacity?: number; is_active?: boolean; }

// src/types/trainer.ts
export interface Trainer { id: number; name: string; email: string; specialization: string | null; availability_notes: string | null; }
export interface TrainerCreate { name: string; email: string; specialization?: string; availability_notes?: string; }
export interface TrainerUpdate { name?: string; email?: string; specialization?: string; availability_notes?: string; }

// src/types/learnerGroup.ts
export interface LearnerGroup { id: number; name: string; size: number; level: string | null; is_active: boolean; }
export interface LearnerGroupCreate { name: string; size: number; level?: string; }
export interface LearnerGroupUpdate { name?: string; size?: number; level?: string; is_active?: boolean; }

// src/types/course.ts
export interface Course { id: number; title: string; description: string | null; total_hours: number; session_duration: number; pedagogical_objectives: string | null; is_active: boolean; }
export interface CourseCreate { title: string; description?: string; total_hours: number; session_duration: number; pedagogical_objectives?: string; }
export interface CourseUpdate { title?: string; description?: string; total_hours?: number; session_duration?: number; pedagogical_objectives?: string; is_active?: boolean; }

// src/types/equipment.ts
export interface Equipment { id: number; name: string; equipment_type: string; quantity: number; is_available: boolean; }
export interface EquipmentCreate { name: string; equipment_type: string; quantity: number; }
export interface EquipmentUpdate { name?: string; equipment_type?: string; quantity?: number; is_available?: boolean; }