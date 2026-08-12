// pages/pedagogical/PedagogicalAuditPage.tsx
// ============================================
// Chef d'orchestre de l'interface.
// Zéro logique métier ici — tout vient du hook usePedagogicalAudit().
//
// Structure :
//   <AuditHeader />        ← titre + bouton "Audit Planning"
//   <AuditScore />         ← gauge circulaire + grade
//   <AuditSummary />       ← vue synthétique 3 colonnes
//   <AuditPlanningView />  ← timeline du planning colorée par résultat d'audit
//   <CriteriaTable />      ← tableau cliquable de tous les critères
//   <RecommendationList /> ← liste numérotée des recommandations

import { useState }            from "react";
import { useLocation }         from "react-router-dom";

import AuditHeader             from "../components/pedagogical/AuditHeader";
import AuditScore              from "../components/pedagogical/AuditScore";
import AuditSummary            from "../components/pedagogical/AuditSummary";
import AuditPlanningView       from "../components/pedagogical/AuditPlanningView";
import CriteriaTable           from "../components/pedagogical/CriteriaTable";
import RecommendationList      from "../components/pedagogical/RecommendationList";
import CriterionCard           from "../components/pedagogical/CriterionCard";

import { usePedagogicalAudit } from "../hooks/usepedagogicalAudit";
import type { CriterionResult } from "../types/pedagogical";
import type { SessionSlot, Constraints } from "../types/planning";


export default function PedagogicalAuditPage() {
  const location = useLocation();
  const navState = location.state as {
    preloadedSchedule?: SessionSlot[];
    preloadedConstraints?: Constraints | null;
  } | null;
  const preloadedSchedule = Array.isArray(navState?.preloadedSchedule) ? navState.preloadedSchedule : [];

  // ── All state + API calls come from the hook ─────────────────────────────
  const {
    status,
    report,
    error,
    isLoading,
    hasReport,
    isCompliant,
    failedCriteria,
    passedCriteria,
    highViolations,
    runAudit,
    fetchReport,
    reset,
  } = usePedagogicalAudit();

  // ── Local UI state — selected criterion for detail card ───────────────────
  const [selected, setSelected] = useState<CriterionResult | null>(null);

  // ── Handler: audit cached report or run from preloaded schedule ───────────
  const handleAudit = () => {
    setSelected(null);
    if (report?.planning_id != null) {
      void fetchReport(report.planning_id);
      return;
    }

    if (preloadedSchedule.length > 0) {
      void runAudit({
        schedule: preloadedSchedule,
        planning_id: report?.planning_id ?? undefined,
      });
    }
  };

  // ── All criteria combined (failed first) ──────────────────────────────────
  const allCriteria = [...failedCriteria, ...passedCriteria];


  // ── RENDER ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50">

      {/* ── Page header bar ─────────────────────────────────────────────── */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center gap-3">
          <span className="text-2xl">📋</span>
          <div>
            <h1 className="text-lg font-bold text-slate-900">Pedagogical Agent</h1>
            <p className="text-xs text-slate-500">
              Audit based on ISO 21001:2018 · ISO 29993:2017
            </p>
          </div>
          {hasReport && report && (
            <span className={`ml-auto rounded-full border px-4 py-1 text-xs font-semibold ${
              isCompliant
                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                : "border-rose-200   bg-rose-50   text-rose-700"
            }`}>
              {isCompliant ? "✅ Compliant" : "❌ Non-Compliant"}
            </span>
          )}
        </div>
      </div>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main className="mx-auto max-w-6xl px-6 py-8 space-y-6">

        {/* Error banner */}
        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800">
            ❌ {error}
          </div>
        )}

        {/* ── 1. AUDIT HEADER ─── always visible */}
        <AuditHeader
          groupName     = {report?.group_name}
          planningId    = {report?.planning_id}
          totalSessions = {report?.total_sessions ?? 0}
          totalHours    = {report?.total_hours    ?? 0}
          isLoading     = {isLoading}
          hasReport     = {hasReport}
          canAudit      = {preloadedSchedule.length > 0 || report?.planning_id != null}
          onAudit       = {handleAudit}
          onReset       = {() => { reset(); setSelected(null); }}
        />

        {/* Loading state */}
        {isLoading && (
          <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-sm">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full
                            border-4 border-slate-200 border-t-slate-800" />
            <p className="text-sm font-semibold text-slate-700">
              Running pedagogical audit…
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Validators → Scoring → LLM explanation
            </p>
            {/* Step hints */}
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {['Workload','Breaks','Progression','Practice','Teacher','Room','Score','Explain'].map(s => (
                <span key={s}
                  className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── RESULTS — shown after successful audit ──────────────────────── */}
        {hasReport && report && !isLoading && (
          <>
            {/* ── 2-column layout: Score + Summary ── */}
            <div className="grid gap-6 lg:grid-cols-2">

              {/* ── 2. AUDIT SCORE ─── grade + gauge */}
              <AuditScore
                score          = {report.score}
                grade          = {report.grade}
                isCompliant    = {report.is_compliant}
                complianceRate = {report.compliance_rate}
                highViolations = {report.high_violations}
              />

              {/* ── 3. AUDIT SUMMARY ─── 3-column synthetic view */}
              <AuditSummary
                totalCriteria  = {report.total_criteria}
                passedCriteria = {report.passed_criteria}
                failedCriteria = {report.failed_criteria}
                highViolations = {report.high_violations}
                totalSessions  = {report.total_sessions}
                totalHours     = {report.total_hours}
              />
            </div>

            {/* ── 4. PLANNING VIEW ─── timeline colored by audit */}
            <AuditPlanningView
              sessions = {report.criteria}   // criteria carry session context in details
              criteria = {report.criteria}
            />

            {/* ── 5+6. SIDE-BY-SIDE: Criteria table + Criterion detail ── */}
            <div className="grid gap-6 lg:grid-cols-[1fr_420px]">

              {/* Left: full criteria table — click → right panel */}
              <CriteriaTable
                criteria        = {allCriteria}
                onSelectCriterion = {setSelected}
                selectedRule    = {selected?.rule ?? null}
              />

              {/* Right: detail card OR recommendations */}
              <div className="space-y-6">
                {selected ? (
                  <CriterionCard
                    criterion = {selected}
                    onClose   = {() => setSelected(null)}
                  />
                ) : (
                  /* ── 7. RECOMMENDATIONS ─── numbered list from backend */
                  <RecommendationList recommendations={report.recommendations} />
                )}
              </div>
            </div>

            {/* ISO references footer */}
            <div className="flex flex-wrap gap-2 pt-2">
              {report.iso_references.map(ref => (
                <span key={ref}
                  className="rounded-full border border-violet-200 bg-violet-50
                             px-3 py-0.5 text-xs font-medium text-violet-700">
                  {ref}
                </span>
              ))}
            </div>
          </>
        )}

      </main>
    </div>
  );
}
