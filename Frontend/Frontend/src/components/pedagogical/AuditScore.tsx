// components/pedagogical/AuditScore.tsx
// ========================================
// Displays the pedagogical score with a circular gauge.
// Receives score + grade from the parent — does NOT calculate anything.

import type { AuditGrade } from "../../types/pedagogical";
import {
  gradeToLabel,
  gradeToColor,
  gradeToBgColor,
  scoreToDegrees,
  complianceBadge,
} from "../../utils/scoreUtils";

interface AuditScoreProps {
  score:          number;       // 0-100
  grade:          AuditGrade;
  isCompliant:    boolean;
  complianceRate: number;       // 0-100
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

  // Color used in the conic gradient
  const gaugeColor: Record<AuditGrade, string> = {
    A: "#059669",   // emerald-600
    B: "#0284c7",   // sky-600
    C: "#d97706",   // amber-600
    D: "#ea580c",   // orange-600
    F: "#dc2626",   // rose-600
  };

  return (
    <div className={`rounded-3xl border ${bgBorder} p-6`}>
      <p className="mb-4 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Audit Score
      </p>

      <div className="flex items-center gap-6">

        {/* Circular gauge */}
        <div
          className="relative flex h-28 w-28 shrink-0 items-center justify-center rounded-full"
          style={{
            background: `conic-gradient(${gaugeColor[grade]} ${degrees}deg, #e2e8f0 ${degrees}deg)`,
          }}
        >
          {/* Inner white circle */}
          <div className="flex h-20 w-20 flex-col items-center justify-center rounded-full bg-white">
            <span className={`text-2xl font-bold leading-none ${color}`}>{grade}</span>
            <span className="text-xs text-slate-400">{score.toFixed(0)}/100</span>
          </div>
        </div>

        {/* Score details */}
        <div className="min-w-0">
          {/* Big score number */}
          <p className={`text-4xl font-bold leading-none ${color}`}>
            {score.toFixed(1)}
            <span className="text-base font-normal text-slate-400">/100</span>
          </p>

          {/* Grade label */}
          <p className={`mt-1 text-sm font-semibold ${color}`}>{label}</p>

          {/* Compliance rate */}
          <p className="mt-1 text-xs text-slate-500">
            {complianceRate.toFixed(0)}% of criteria passed
          </p>

          {/* Compliance badge */}
          <span className={`mt-2 inline-block rounded-full border px-3 py-0.5 text-xs font-semibold ${badge.className}`}>
            {badge.label}
          </span>

          {/* High violations warning */}
          {highViolations > 0 && (
            <p className="mt-2 text-xs font-medium text-rose-600">
              ⚠️ {highViolations} high-severity violation{highViolations > 1 ? "s" : ""}
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-5">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span>0</span>
          <span>50</span>
          <span>100</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width:           `${score}%`,
              backgroundColor: gaugeColor[grade],
            }}
          />
        </div>
      </div>
    </div>
  );
}