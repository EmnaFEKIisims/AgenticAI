// components/pedagogical/AuditScore.tsx
// ========================================
// Displays the pedagogical score with a circular gauge.
// Receives score + grade from the parent — does NOT calculate anything.

import { AlertTriangle } from "lucide-react";
import type { AuditGrade } from "../../types/pedagogical";
import {
  gradeToLabel,
  gradeToColor,
  gradeToBgColor,
  scoreToDegrees,
  complianceBadge,
} from "../../utils/scoreUtils";

interface AuditScoreProps {
  score:          number;
  grade:          AuditGrade;
  isCompliant:    boolean;
  complianceRate: number;
  highViolations: number;
}

export default function AuditScore({
  score,
  grade,
  isCompliant,
  complianceRate,
  highViolations,
}: AuditScoreProps) {
  const degrees    = scoreToDegrees(score);
  const color      = gradeToColor(grade);
  const bgBorder   = gradeToBgColor(grade);
  const label      = gradeToLabel(grade);
  const badge      = complianceBadge(isCompliant);

  const gaugeColor: Record<AuditGrade, string> = {
    A: "#10b981",
    B: "#78a6c6",
    C: "#a48bc2",
    D: "#c9829a",
    F: "#bf6f84",
  };

  return (
    <div className={`ped-score-card grade-${grade} overflow-hidden rounded-3xl border ${bgBorder} bg-white shadow-sm`}>
      <div className="p-6">
        <p className="mb-5 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Audit score
        </p>

        <div className="flex items-center gap-6">
          {/* Circular gauge */}
          <div
            className="relative flex h-28 w-28 shrink-0 items-center justify-center rounded-full"
            style={{
              background: `conic-gradient(${gaugeColor[grade]} ${degrees}deg, #e2e8f0 ${degrees}deg)`,
            }}
          >
            <div className="flex h-20 w-20 flex-col items-center justify-center rounded-full bg-white shadow-inner">
              <span className={`text-2xl font-bold leading-none ${color}`}>{grade}</span>
              <span className="mt-0.5 font-mono text-[10px] text-slate-400">
                {score.toFixed(0)}/100
              </span>
            </div>
          </div>

          {/* Details */}
          <div className="min-w-0 flex-1">
            <p className={`text-4xl font-bold leading-none ${color}`}>
              {score.toFixed(1)}
              <span className="ml-0.5 text-base font-normal text-slate-400">/100</span>
            </p>

            <p className={`mt-1.5 text-sm font-semibold ${color}`}>{label}</p>

            <p className="mt-1 text-xs text-slate-500">
              {complianceRate.toFixed(0)}% of criteria passed
            </p>

            <span className={`ped-compliance-badge mt-2.5 inline-flex items-center gap-1.5 rounded-full border px-3 py-0.5 text-xs font-semibold ${badge.className}`}>
              {badge.label}
            </span>

            {highViolations > 0 && (
              <p className="ped-violations mt-2.5 inline-flex items-center gap-1.5 text-xs font-medium text-rose-600">
                <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                {highViolations} high-severity violation{highViolations > 1 ? "s" : ""}
              </p>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6">
          <div className="mb-1.5 flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-slate-400">
            <span>0</span>
            <span>50</span>
            <span>100</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${score}%`, backgroundColor: gaugeColor[grade] }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}