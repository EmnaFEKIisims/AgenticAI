// src/pages/DataPage.tsx
import React, { useState, useCallback } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadResponse, 
  PreviewResponse, 
  ValidationIssue, 
  PreviewRecord 
} from '../types/dataManager';
import { dataApi } from '../services/dataManagerService';

import FileUpload from '../components/data/FileUpload';
import DataPreviewTable from '../components/data/DataPreviewTable';
import DataActions from '../components/data/DataActions';
import DataStatus from '../components/data/DataStatus';

const DataPage: React.FC = () => {
  const navigate = useNavigate();

  // ====================== STATE ======================
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<PreviewRecord[]>([]);
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'preview' | 'validated' | 'rejected'>('idle');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>('');

  // ====================== HANDLERS ======================

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
  };

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setStatus('uploading');

    try {
      const response: UploadResponse = await dataApi.uploadFile(selectedFile);

      setUploadId(response.upload_id);
      setFilename(response.filename);
      setPreviewData(response.preview);
      setIssues(response.issues);
      setStatus('preview');

      console.log(`✅ Upload successful - ID: ${response.upload_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to upload file');
      setStatus('idle');
    } finally {
      setLoading(false);
      setSelectedFile(null); // Reset file input after upload
    }
  }, [selectedFile]);

  const handleRefreshPreview = useCallback(async () => {
    if (!uploadId) return;

    setLoading(true);
    try {
      const response: PreviewResponse = await dataApi.getPreview(uploadId);
      setPreviewData(response.preview);
      setStatus('preview');
    } catch (err: any) {
      setError(err.message || 'Failed to refresh preview');
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const handleValidate = useCallback(async () => {
    if (!uploadId) return;

    setLoading(true);
    setError(null);

    try {
      await dataApi.validateData(uploadId);
      setStatus('validated');
      alert('✅ Data successfully validated and inserted into the database!');
    } catch (err: any) {
      setError(err.message || 'Validation failed');
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const handleReject = useCallback(async () => {
    if (!uploadId) return;

    if (!window.confirm('Are you sure you want to reject this data? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await dataApi.rejectData(uploadId);
      setStatus('rejected');
      setUploadId(null);
      setPreviewData([]);
      setIssues([]);
      alert('❌ Data rejected and cleared.');
    } catch (err: any) {
      setError(err.message || 'Reject failed');
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const handleUpdateData = useCallback(async (updatedData: PreviewRecord[]) => {
    if (!uploadId) return;

    setLoading(true);
    setError(null);

    try {
      await dataApi.updateData(uploadId, updatedData);
      setPreviewData(updatedData);
      setStatus('preview');
      alert('✅ Data has been updated successfully. You can now validate it.');
    } catch (err: any) {
      setError(err.message || 'Update failed');
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  const handleReset = () => {
    setUploadId(null);
    setPreviewData([]);
    setIssues([]);
    setStatus('idle');
    setError(null);
    setFilename('');
    setSelectedFile(null);
  };

  // ====================== RENDER ======================
  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      <div>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition"
          aria-label="Back to home"
        >
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Back to home</span>
        </button>
      </div>

      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Data Manager
        </h1>
        <p className="text-gray-600 text-lg">
          Upload • Extract • Validate • Import your training data
        </p>
      </div>

      {/* Status Banner */}
      <DataStatus 
        status={status} 
        loading={loading} 
        error={error} 
        filename={filename}
      />

      {/* File Upload Section */}
      {status === 'idle' || status === 'rejected' ? (
        <FileUpload 
          onFileSelect={handleFileSelect}
          onUpload={handleUpload}
          selectedFile={selectedFile}
          loading={loading}
        />
      ) : null}

      {/* Preview & Actions */}
      {(status === 'preview' || status === 'validated') && uploadId && (
        <div className="space-y-6">
          <DataActions
            status={status}
            onValidate={handleValidate}
            onReject={handleReject}
            onReset={handleReset}
            onRefresh={handleRefreshPreview}
            loading={loading}
          />

          <DataPreviewTable
            data={previewData}
            issues={issues}
            onDataUpdate={handleUpdateData}
            loading={loading}
          />
        </div>
      )}

      {/* Success Message after validation */}
      {status === 'validated' && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
          <h2 className="text-2xl font-semibold text-green-800 mb-2">
            🎉 Import Completed Successfully
          </h2>
          <p className="text-green-700 mb-6">
            Your data has been inserted into the database.
          </p>
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            Start New Import
          </button>
        </div>
      )}
    </div>
  );
};

export default DataPage;