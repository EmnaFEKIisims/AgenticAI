// src/pages/DataPage.tsx
import React, { useState, useCallback } from 'react';
import { CheckCircle2, Eye, FileUp, PencilLine } from 'lucide-react';
import '../styles/data.css';
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

      console.log(`Upload successful - ID: ${response.upload_id}`);
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
      alert('Data successfully validated and inserted into the database!');
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
      alert('Data rejected and cleared.');
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
      alert('Data has been updated successfully. You can now validate it.');
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
      <header className="data-header border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="data-header-inner mx-auto flex max-w-4xl items-center gap-4 px-6 py-5">
          <span className="data-header-icon bg-primary! text-primary-content! flex h-11 w-11 shrink-0 items-center justify-center rounded-xl shadow-sm" aria-hidden="true">
            <FileUp className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <h1>Data manager</h1>
            <p>Import your source data, review the records, and prepare your planning.</p>
          </div>
        </div>
      </header>

      <main className="data-main mx-auto max-w-4xl space-y-6 px-6 py-10">
        <section className="data-process" aria-label="Import process">
          <div className="data-process-intro">
            <p className="data-process-kicker">Simple and controlled</p>
            <h2>From file to planning data</h2>
          </div>
          <div className="data-process-steps">
            <div className="data-process-step data-process-step-active">
              <span className="data-process-number">01</span>
              <span className="data-process-icon"><FileUp className="h-4 w-4" /></span>
              <span><strong>Upload</strong><small>Choose a source file</small></span>
            </div>
            <div className="data-process-connector" />
            <div className="data-process-step">
              <span className="data-process-number">02</span>
              <span className="data-process-icon"><Eye className="h-4 w-4" /></span>
              <span><strong>Review</strong><small>Check extracted records</small></span>
            </div>
            <div className="data-process-connector" />
            <div className="data-process-step">
              <span className="data-process-number">03</span>
              <span className="data-process-icon"><CheckCircle2 className="h-4 w-4" /></span>
              <span><strong>Validate</strong><small>Approve the import</small></span>
            </div>
          </div>
        </section>

        <div className="data-assurance-row" aria-label="Import details">
          <div className="data-assurance-item">
            <span className="data-assurance-icon data-assurance-icon-blue"><Eye className="h-4 w-4" /></span>
            <span><strong>Preview first</strong><small>Nothing is imported automatically</small></span>
          </div>
          <div className="data-assurance-item">
            <span className="data-assurance-icon data-assurance-icon-lilac"><PencilLine className="h-4 w-4" /></span>
            <span><strong>Review records</strong><small>Correct extracted values inline</small></span>
          </div>
          <div className="data-assurance-item">
            <span className="data-assurance-icon data-assurance-icon-green"><CheckCircle2 className="h-4 w-4" /></span>
            <span><strong>Validate when ready</strong><small>Keep full control of the import</small></span>
          </div>
        </div>

        <section className="data-workspace-card overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="data-workspace-heading flex items-center justify-between gap-4 border-b border-slate-200 px-6 py-5">
            <div className="flex min-w-0 items-center gap-4">
              <span className="data-workspace-icon flex h-11 w-11 shrink-0 items-center justify-center rounded-xl" aria-hidden="true">
                <FileUp className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <span className="data-heading-kicker">Source data</span>
                <h2>Import your training data</h2>
                <p>Upload a file, inspect the preview, then validate the records.</p>
              </div>
            </div>
            <span className="data-format-note hidden shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium sm:inline-flex">
              CSV / Excel / PDF
            </span>
          </div>

          <div className="data-workspace-body space-y-4 p-6">
            <DataStatus status={status} loading={loading} error={error} filename={filename} />

            {(status === 'idle' || status === 'rejected') && (
              <FileUpload onFileSelect={handleFileSelect} onUpload={handleUpload} selectedFile={selectedFile} loading={loading} />
            )}

            {(status === 'preview' || status === 'validated') && uploadId && (
              <div className="data-result-stack">
                <DataActions status={status} onValidate={handleValidate} onReject={handleReject} onReset={handleReset} onRefresh={handleRefreshPreview} loading={loading} />
                <DataPreviewTable data={previewData} issues={issues} onDataUpdate={handleUpdateData} loading={loading} />
              </div>
            )}

            {status === 'validated' && (
              <div className="data-success-panel">
                <div className="data-success-mark">✓</div>
                <div>
                  <h2>Import completed successfully</h2>
                  <p>Your data has been inserted into the database.</p>
                </div>
                <button onClick={handleReset} className="data-success-button">Start New Import</button>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
};

export default DataPage;