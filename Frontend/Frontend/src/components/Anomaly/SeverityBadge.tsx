// components/anomaly/SeverityBadge.tsx
import type { AnomalySeverity } from "../../types/anomaly";
import { severityLabel, severityIcon, severityColor } from "../../utils/anomalyUtils";

interface SeverityBadgeProps {
  severity: AnomalySeverity;
  showIcon?: boolean;
}

export default function SeverityBadge({ severity, showIcon = true }: SeverityBadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${severityColor(severity)}`}>
      {showIcon && <span>{severityIcon(severity)}</span>}
      {severityLabel(severity)}
    </span>
  );
}