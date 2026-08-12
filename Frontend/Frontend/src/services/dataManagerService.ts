// src/api/dataApi.ts
// =====================================================
// API Client pour le Data Manager (DataAgent)
// Toutes les interactions avec /data/* endpoints
// =====================================================

import { 
  UploadResponse, 
  PreviewResponse, 
  ValidateResponse, 
  RejectResponse, 
  UpdateRequest, 
  UpdateResponse 
} from '../types/dataManager';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Helper centralisé pour gérer les erreurs et le JSON
 */
async function apiFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 🔹 1. Upload a file (CSV, Excel or PDF)
 * POST /data/upload
 */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/data/upload`, {
    method: 'POST',
    body: formData,
    // Ne pas mettre Content-Type → le navigateur le gère automatiquement pour FormData
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed: ${response.status}`);
  }

  return response.json();
}

/**
 * 🔹 2. Get preview of extracted data
 * GET /data/preview/{upload_id}
 */
export async function getPreview(upload_id: string): Promise<PreviewResponse> {
  return apiFetch<PreviewResponse>(`/data/preview/${upload_id}`);
}

/**
 * 🔹 3. Validate data (HITL - Approve)
 * POST /data/validate/{upload_id}
 */
export async function validateData(upload_id: string): Promise<ValidateResponse> {
  return apiFetch<ValidateResponse>(`/data/validate/${upload_id}`, {
    method: 'POST',
  });
}

/**
 * 🔹 4. Reject data
 * POST /data/reject/{upload_id}
 */
export async function rejectData(upload_id: string): Promise<RejectResponse> {
  return apiFetch<RejectResponse>(`/data/reject/${upload_id}`, {
    method: 'POST',
  });
}

/**
 * 🔹 5. Update / Correct data manually
 * PUT /data/update/{upload_id}
 */
export async function updateData(
  upload_id: string, 
  data: UpdateRequest['data']
): Promise<UpdateResponse> {
  return apiFetch<UpdateResponse>(`/data/update/${upload_id}`, {
    method: 'PUT',
    body: JSON.stringify({ data }),
  });
}

// =====================================================
// Export groupé pour utilisation facile dans le hook
// =====================================================
export const dataApi = {
  uploadFile,
  getPreview,
  validateData,
  rejectData,
  updateData,
} as const;