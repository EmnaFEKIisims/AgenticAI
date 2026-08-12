export interface UploadResponse {
  success: boolean;
  upload_id: string;
  filename: string;
  status: "pending_review" | "corrected" | "approved" | "rejected"; // ajouté par le router
  total_raw: number;
  total_valid: number;
  total_invalid: number;
  preview: PreviewRecord[];           // premiers enregistrements valides
  issues: ValidationIssue[];
  error?: string;
}

/**
 * Un enregistrement dans le preview (après flattening + nettoyage)
 * Chaque record contient entity_type + les champs DB-ready
 */
export interface PreviewRecord {
  entity_type: "course" | "trainer" | "room" | "group" | "equipment" | "constraint";
  [key: string]: any; // les autres champs (name, title, capacity, etc.)
}

/**
 * Structure exacte d'une issue de validation (comme construit dans data_agent.py)
 */
export interface ValidationIssue {
  entity_type: string;
  issues: string[];           // ex: ["Missing required field: 'name'", "Email format invalid"]
  record: Record<string, any>; // le record original qui pose problème
}

/**
 * Réponse de GET /data/preview/{id}
 * (le router renvoie généralement les mêmes données que upload)
 */
export interface PreviewResponse {
  upload_id: string;
  filename: string;
  status: string;
  preview: PreviewRecord[];
  issues: ValidationIssue[];
  total_valid: number;
  total_invalid: number;
  data: PreviewRecord[];
}

/**
 * Réponse de POST /data/validate/{id}
 */
export interface ValidateResponse {
  success: boolean;
  upload_id: string;
  status: "approved";
  message: string;
  inserted?: {
    courses: number;
    trainers: number;
    rooms: number;
    groups: number;
    equipment: number;
    constraints: number;
  };
}

/**
 * Réponse de POST /data/reject/{id}
 */
export interface RejectResponse {
  success: boolean;
  upload_id: string;
  status: "rejected";
  message: string;
}

/**
 * Body pour PUT /data/update/{id} (correction manuelle avant validation)
 * Le frontend envoie la liste complète des records corrigés (flat)
 */
export interface UpdateRequest {
  data: PreviewRecord[];   // liste plate des records corrigés
}

/**
 * Réponse après mise à jour (le router renvoie généralement le nouvel état)
 */
export interface UpdateResponse {
  success: boolean;
  upload_id: string;
  status: "corrected";
  message: string;
  preview: PreviewRecord[];
  issues: ValidationIssue[]; // issues restantes après correction
}

/**
 * Union type utile dans le hook pour gérer tous les états de upload
 */
export type DataManagerResponse =
  | UploadResponse
  | PreviewResponse
  | ValidateResponse
  | RejectResponse
  | UpdateResponse;