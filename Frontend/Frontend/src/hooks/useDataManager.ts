// src/hooks/useDataManager.ts
import { useState, useCallback } from 'react';
import { 
  UploadResponse, 
  PreviewResponse, 
  ValidateResponse, 
  RejectResponse, 
  UpdateResponse, 
  PreviewRecord, 
  ValidationIssue 
} from '../types/dataManager';
import { dataApi } from '../services/dataManagerService';

type DataStatus = 'idle' | 'uploading' | 'preview' | 'validated' | 'rejected' | 'error';

export const useDataManager = () => {
  // ====================== STATE ======================
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>('');
  const [previewData, setPreviewData] = useState<PreviewRecord[]>([]);
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [status, setStatus] = useState<DataStatus>('idle');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ====================== ACTIONS ======================

  const uploadFile = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    setStatus('uploading');

    try {
      const response: UploadResponse = await dataApi.uploadFile(file);

      setUploadId(response.upload_id);
      setFilename(response.filename);
      setPreviewData(response.preview);
      setIssues(response.issues || []);
      setStatus('preview');

      return response;
    } catch (err: any) {
      const errorMessage = err.message || "Échec de l'upload du fichier";
      setError(errorMessage);
      setStatus('error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshPreview = useCallback(async () => {
    if (!uploadId) return;

    setLoading(true);
    setError(null);

    try {
      const response: PreviewResponse = await dataApi.getPreview(uploadId);
      
      // Correction ici : le backend renvoie "data", pas "preview"
      setPreviewData(response.data || []);
      setStatus('preview');
    } catch (err: any) {
      const errorMessage = err.message || 'Impossible de rafraîchir la prévisualisation';
      setError(errorMessage);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const validateData = useCallback(async () => {
    if (!uploadId) return;

    setLoading(true);
    setError(null);

    try {
      const response: ValidateResponse = await dataApi.validateData(uploadId);
      setStatus('validated');
      return response;
    } catch (err: any) {
      const errorMessage = err.message || 'Échec de la validation';
      setError(errorMessage);
      setStatus('error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const rejectData = useCallback(async () => {
    if (!uploadId) return;

    setLoading(true);
    setError(null);

    try {
      await dataApi.rejectData(uploadId);
      setStatus('rejected');
      // Reset state
      setUploadId(null);
      setPreviewData([]);
      setIssues([]);
      setFilename('');
    } catch (err: any) {
      const errorMessage = err.message || 'Échec du rejet';
      setError(errorMessage);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const updateData = useCallback(async (updatedData: PreviewRecord[]) => {
    if (!uploadId) return;

    setLoading(true);
    setError(null);

    try {
      await dataApi.updateData(uploadId, updatedData);
      setPreviewData(updatedData);
      setStatus('preview');
    } catch (err: any) {
      const errorMessage = err.message || 'Échec de la mise à jour';
      setError(errorMessage);
      setStatus('error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const reset = useCallback(() => {
    setUploadId(null);
    setFilename('');
    setPreviewData([]);
    setIssues([]);
    setStatus('idle');
    setError(null);
  }, []);

  // ====================== DERIVED VALUES ======================
  const hasData = previewData.length > 0;
  const canValidate = status === 'preview' && hasData;
  const canReject = ['preview', 'validated'].includes(status);
  const hasIssues = issues.length > 0;

  return {
    // State
    uploadId,
    filename,
    previewData,
    issues,
    status,
    loading,
    error,

    // Derived
    hasData,
    canValidate,
    canReject,
    hasIssues,

    // Actions
    uploadFile,
    refreshPreview,
    validateData,
    rejectData,
    updateData,
    reset,
  };
};