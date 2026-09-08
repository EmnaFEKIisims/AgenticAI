/// <reference types="vite/client" />
// src/services/crudServices.ts
// All 6 entity services — same pattern, different endpoint.

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
           ?? "http://localhost:8000";

async function call<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    let d = `HTTP ${res.status}`;
    try { const b = await res.json(); d = b?.detail ?? d; } catch {}
    throw new Error(d);
  }
  return res.json() as Promise<T>;
}

// ── ROOM ─────────────────────────────────────────────────────────────────────
export const getRooms       = ()            => call<any[]>("/rooms");
export const getRoom        = (id: number)  => call<any>(`/rooms/${id}`);
export const createRoom     = (b: any)      => call<any>("/rooms",         { method: "POST",   body: JSON.stringify(b) });
export const updateRoom     = (id: number, b: any) => call<any>(`/rooms/${id}`, { method: "PUT",  body: JSON.stringify(b) });
export const deleteRoom     = (id: number)  => call<any>(`/rooms/${id}`,   { method: "DELETE" });

// ── TRAINER ───────────────────────────────────────────────────────────────────
export const getTrainers    = ()            => call<any[]>("/trainers");
export const getTrainer     = (id: number)  => call<any>(`/trainers/${id}`);
export const createTrainer  = (b: any)      => call<any>("/trainers",      { method: "POST",   body: JSON.stringify(b) });
export const updateTrainer  = (id: number, b: any) => call<any>(`/trainers/${id}`, { method: "PUT",  body: JSON.stringify(b) });
export const deleteTrainer  = (id: number)  => call<any>(`/trainers/${id}`,{ method: "DELETE" });


// ── LEARNER GROUP ─────────────────────────────────────────────────────────────
export const getGroups      = ()            => call<any[]>("/learner-groups");
export const getGroup       = (id: number)  => call<any>(`/learner-groups/${id}`);
export const createGroup    = (b: any)      => call<any>("/learner-groups", { method: "POST",  body: JSON.stringify(b) });
export const updateGroup    = (id: number, b: any) => call<any>(`/learner-groups/${id}`, { method: "PUT",  body: JSON.stringify(b) });
export const deleteGroup    = (id: number)  => call<any>(`/learner-groups/${id}`, { method: "DELETE" });

// ── COURSE ────────────────────────────────────────────────────────────────────
export const getCourses     = ()            => call<any[]>("/courses");
export const getCourse      = (id: number)  => call<any>(`/courses/${id}`);
export const createCourse   = (b: any)      => call<any>("/courses",       { method: "POST",   body: JSON.stringify(b) });
export const updateCourse   = (id: number, b: any) => call<any>(`/courses/${id}`, { method: "PUT",  body: JSON.stringify(b) });
export const deleteCourse   = (id: number)  => call<any>(`/courses/${id}`, { method: "DELETE" });

// ── EQUIPMENT ─────────────────────────────────────────────────────────────────
export const getEquipments  = ()            => call<any[]>("/equipment");
export const getEquipment   = (id: number)  => call<any>(`/equipment/${id}`);
export const createEquipment= (b: any)      => call<any>("/equipment",     { method: "POST",   body: JSON.stringify(b) });
export const updateEquipment= (id: number, b: any) => call<any>(`/equipment/${id}`, { method: "PUT",  body: JSON.stringify(b) });
export const deleteEquipment= (id: number)  => call<any>(`/equipment/${id}`,{ method: "DELETE" });