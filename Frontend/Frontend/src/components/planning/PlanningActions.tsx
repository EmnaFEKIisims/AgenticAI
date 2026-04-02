import type { PlanningState } from "../../types/planning";
import Button from "../ui/Button";

interface PlanningActionsProps {
  status: PlanningState["status"];
  onValidate: () => void;
  onExport: () => void;
  loading: boolean;
}

export default function PlanningActions({
  status,
  onValidate,
  onExport,
  loading,
}: PlanningActionsProps) {
  return (
    <div className="planning-action-bar">
      {status === "success" && (
        <Button
          className="planning-btn planning-btn-success"
          onClick={onValidate}
          disabled={loading}
        >
           Validate Schedule
        </Button>
      )}

      {(status === "success" || status === "validated") && (
        <Button
          className="planning-btn planning-btn-export"
          onClick={onExport}
          disabled={loading}
        >
           Export CSV
        </Button>
      )}
    </div>
  );
}
