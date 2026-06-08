import { ChangeEvent } from 'react';

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
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Upload Your File</h2>
      <p className="text-sm text-gray-600 mb-5">
        Supported formats: CSV, Excel (XLS/XLSX), and PDF.
      </p>

      <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
        <input
          type="file"
          accept=".csv,.xls,.xlsx,.pdf"
          onChange={handleChange}
          disabled={loading}
          className="block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />

        <button
          type="button"
          onClick={onUpload}
          disabled={!selectedFile || loading}
          className="px-5 py-2 rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
        >
          {loading ? 'Uploading...' : 'Upload & Preview'}
        </button>
      </div>

      {selectedFile && (
        <p className="mt-4 text-sm text-gray-700">
          Selected file: <span className="font-medium">{selectedFile.name}</span>
        </p>
      )}
    </section>
  );
}
