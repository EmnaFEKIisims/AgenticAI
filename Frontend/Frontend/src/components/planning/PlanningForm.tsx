import Button from "../ui/Button";
import Card from "../ui/Card";
import Input from "../ui/Input";
import { ClipboardList, Loader2, Play } from "lucide-react";

interface PlanningFormProps {
  value: string;
  onChange: (value: string) => void;
  onRun: () => void;
  disabled: boolean;
  loading: boolean;
}

export default function PlanningForm({
  value,
  onChange,
  onRun,
  disabled,
  loading,
}: PlanningFormProps) {
  return (
    <Card className="planning-input-card">
      <label className="planning-label">
        <span className="planning-label-icon" aria-hidden="true">
          <ClipboardList size={14} />
        </span>
        Extra Constraints
        <span className="planning-label-sub"> - natural language, English or French (optional)</span>
      </label>

      <Input
        multiline
        rows={4}
        className={`planning-textarea${disabled ? " planning-textarea-disabled" : ""}`}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={
          "e.g. No sessions on Friday.\nAhmed available Monday morning only.\nLab rooms for technical courses."
        }
      />

      <div className="planning-action-bar planning-form-actions">
        <Button
          className="planning-btn planning-btn-primary"
          onClick={onRun}
          disabled={disabled}
        >
          {loading ? (
            <>
              <Loader2 size={14} className="planning-btn-icon planning-spin" aria-hidden="true" />
              Generating...
            </>
          ) : (
            <>
              <Play size={14} className="planning-btn-icon" aria-hidden="true" />
              Run Planning
            </>
          )}
        </Button>
      </div>
    </Card>
  );
}
