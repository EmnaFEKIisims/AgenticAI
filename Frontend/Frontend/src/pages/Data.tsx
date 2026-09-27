// src/pages/DataPage.tsx
import React, { useState, useCallback } from 'react';
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
    <div className="data-page">
      <div className="data-shell">
      <div className="data-breadcrumb-row">
        <span className="data-breadcrumb-label">Data agent / Import center</span>
      </div>

      <div className="data-hero">
        <div className="data-hero-copy">
          <span className="data-eyebrow"><span className="data-eyebrow-dot" /> Data operations</span>
          <h1>Bring your training data into focus.</h1>
          <p>Upload a source file, inspect the extracted records, and approve a clean import into your learning system.</p>
          <div className="data-hero-meta">
            <span><strong>01</strong> Upload</span>
            <span><strong>02</strong> Inspect</span>
            <span><strong>03</strong> Approve</span>
          </div>
        </div>
        <div className="data-pipeline-card" aria-label="Import pipeline">
          <div className="data-pipeline-heading">
            <span>Import pipeline</span>
            <span className="data-live-status"><span /> Ready</span>
          </div>
          <div className="data-pipeline-line" />
          <div className="data-pipeline-steps">
            <div><span className="data-pipeline-number data-pipeline-number-active">01</span><small>Source</small></div>
            <div><span className="data-pipeline-number">02</span><small>Preview</small></div>
            <div><span className="data-pipeline-number">03</span><small>Database</small></div>
          </div>
          <p>Every import stays reviewable before it reaches your database.</p>
        </div>
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
        <div className="data-success-panel">
          <div className="data-success-mark">✓</div>
          <div>
          <h2>
            Import completed successfully
          </h2>
          <p>
            Your data has been inserted into the database.
          </p>
          </div>
          <button
            onClick={handleReset}
            className="data-success-button"
          >
            Start New Import
          </button>
        </div>
      )}
      </div>
    </div>
  );
};

export default DataPage;