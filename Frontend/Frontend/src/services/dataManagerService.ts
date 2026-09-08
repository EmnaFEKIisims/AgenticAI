/// <reference types="vite/client" />
// src/api/dataApi.ts
// Updated: X-User-ID header injected on all requests via central apiFetch
// uploadFile uses FormData (special case — Content-Type not set manually)

import { apiFetch, apiGet, apiPost, apiPut, BASE } from "../services/api";

import type {
  UploadResponse,
  PreviewResponse,
  ValidateResponse,
  RejectResponse,
  UpdateRequest,
  UpdateResponse,
} from "../types/dataManager";

// ── 1. Upload file (CSV / Excel / PDF) ────────────────────────────────────────

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  // Use apiFetch directly so X-User-ID header is injected
  // Do NOT set Content-Type — browser sets it automatically for FormData
  const res = await apiFetch("/data/upload", {
    method: "POST",
    body:   formData,
    headers: {
      // Only X-User-ID will be set by apiFetch internals
      // Content-Type intentionally omitted for FormData
    },
  });

  return res.json() as Promise<UploadResponse>;
}

// ── 2. Preview extracted data ─────────────────────────────────────────────────

export async function getPreview(upload_id: string): Promise<PreviewResponse> {
  return apiGet<PreviewResponse>(`/data/preview/${upload_id}`);
}

// ── 3. Validate / approve (HITL) ──────────────────────────────────────────────
// X-User-ID is critical here — backend uses it to tag every inserted DB record

export async function validateData(upload_id: string): Promise<ValidateResponse> {
  return apiPost<ValidateResponse>(`/data/validate/${upload_id}`);
}

// ── 4. Reject data ────────────────────────────────────────────────────────────

export async function rejectData(upload_id: string): Promise<RejectResponse> {
  return apiPost<RejectResponse>(`/data/reject/${upload_id}`);
}

// ── 5. Update / correct data ──────────────────────────────────────────────────

export async function updateData(
  upload_id: string,
  data:      UpdateRequest["data"],
): Promise<UpdateResponse> {
  return apiPut<UpdateResponse>(`/data/update/${upload_id}`, { data });
}

// ── Grouped export ────────────────────────────────────────────────────────────

export const dataApi = {
  uploadFile,
  getPreview,
  validateData,
  rejectData,
  updateData,
} as const;