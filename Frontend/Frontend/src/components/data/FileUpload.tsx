import { ChangeEvent, useRef } from 'react';
import { UploadCloud, FileText, Loader2 } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onUpload: () => void;
  selectedFile: File | null;
  loading: boolean;
}

export default function FileUpload({
  onFileSelect,
  onUpload,
  selectedFile,
  loading,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <section className="data-panel data-upload-panel">
      {/* Header */}
      <header className="data-panel-header">
        <span className="data-icon-tile data-icon-tile-coral">
          <UploadCloud className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h2>
            Upload your file
          </h2>
          <p>
            Supported formats: CSV, Excel (XLS / XLSX) and PDF.
          </p>
        </div>
      </header>

      {/* Body */}
      <div className="data-panel-body">
        {/* Dropzone */}
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={loading}
          className="data-dropzone group"
        >
          <span className="data-dropzone-icon">
            <UploadCloud className="h-6 w-6" aria-hidden="true" />
          </span>
          <div className="space-y-1">
            <p>
              Click to browse your files
            </p>
            <p>
              CSV · XLS · XLSX · PDF
            </p>
          </div>
        </button>

        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xls,.xlsx,.pdf"
          onChange={handleChange}
          disabled={loading}
          className="hidden"
        />

        {/* Selected file + upload */}
        <div className="data-upload-footer">
          <div className="min-w-0 flex-1">
            {selectedFile ? (
              <div className="data-selected-file">
                <span className="data-file-icon">
                  <FileText className="h-4 w-4" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p>
                    {selectedFile.name}
                  </p>
                  <p>
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
            ) : (
              <p className="data-muted-copy">
                No file selected yet.
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onUpload}
            disabled={!selectedFile || loading}
            className="data-primary-button"
          >
            {loading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                Uploading…
              </>
            ) : (
              <>
                <UploadCloud className="h-4 w-4" aria-hidden="true" />
                Upload & preview
              </>
            )}
          </button>
        </div>
      </div>
    </section>
  );
}