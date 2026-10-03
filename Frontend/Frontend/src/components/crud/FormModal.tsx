// src/components/crud/FormModal.tsx
// Wraps any entity form in a modal overlay.

interface Props {
  title:    string;
  onClose:  () => void;
  children: React.ReactNode;
}

export default function FormModal({ title, onClose, children }: Props) {
  return (
    <div className="crud-modal-overlay">
      <div className="crud-modal">
        {/* Header */}
        <div className="crud-modal-header">
          <h2>{title}</h2>
          <button onClick={onClose}
            className="crud-modal-close">
            ✕
          </button>
        </div>
        {/* Body */}
        <div className="crud-modal-body">
          {children}
        </div>
      </div>
    </div>
  );
}