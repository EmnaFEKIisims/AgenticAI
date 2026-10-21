// pages/pedagogical/PedagogicalAuditPage.tsx
// ============================================
// Chef d'orchestre de l'interface.
// Zéro logique métier ici — tout vient du hook usePedagogicalAudit().
//
// ← REDESIGNED: the page used to dump three things nobody asked for:
//   (1) a grid of every single session marked "conforme" — its status
//       was hardcoded to "passed" in toAuditPlanningItem(), so it never
//       reflected the real audit and was pure noise, AND it was the
//       heaviest thing on the page to render (up to 200+ session cards),
//   (2) the AI's readable narrative paragraph buried as item #1 inside a
//       generic numbered "recommendations" list, indistinguishable from
//       the raw scoring-service action items,
//   (3) a full raw criteria table shown open by default, pushing the
//       actually useful content below the fold.
//
//   New structure — a real executive report, short by default:
//     <AuditHeader />          ← titre + bouton "Audit Planning"
//     <AuditScore /> + <NarrativeSummary />  ← verdict en un coup d'œil
//     <AuditSummary />         ← chiffres clés
//     <KeyFindings />          ← 3 points forts / 3 points à corriger
//     <RecommendationList />   ← plan d'action concret (sans le narratif)
//     <CriteriaTable />        ← replié par défaut, pour les curieux
//     <CriterionCard />        ← détail au clic

import { useEffect, useMemo, useRef, useState } from "react";
import { ClipboardCheck } from "lucide-react";
import { useLocation }         from "react-router-dom";

import AuditHeader             from "../components/pedagogical/AuditHeader";
import AuditScore              from "../components/pedagogical/AuditScore";
import AuditSummary            from "../components/pedagogical/AuditSummary";
import NarrativeSummary from "../components/pedagogical/NarrativeSummary";
import KeyFindings from "../components/pedagogical/KeyFindings";
import CriteriaTable           from "../components/pedagogical/CriteriaTable";
import RecommendationList      from "../components/pedagogical/RecommendationList";
import CriterionCard           from "../components/pedagogical/CriterionCard";

import { usePedagogicalAudit } from "../hooks/usepedagogicalAudit";
import type { CriterionResult } from "../types/pedagogical";
import type { SessionSlot, Constraints } from "../types/planning";
import "../styles/pedagogical.css";


const PEDAGOGICAL_CACHE_KEY = "pedagogical-audit-cache-v1";

// ← ADDED: a cheap, stable fingerprint of "what schedule is this". We don't
//   need a cryptographic hash — just something that changes whenever the
//   set of sessions, their slots, or their validation status changes, so we
//   can tell a *stale* cached report from one that still matches what's on
//   screen. id + start_time + status covers every case that actually
//   changes the audit outcome (a move changes start_time, a validate/reject
//   changes status, adding/removing sessions changes the id set).
function fingerprintSchedule(schedule: SessionSlot[]): string {
  return schedule
    .map((s) => `${s.id ?? s.session_number}:${s.start_time}:${s.status}`)
    .sort()
    .join("|");
}

function readCachedAudit(): {
  schedule: SessionSlot[];
  report: ReturnType<typeof JSON.parse> | null;
  scheduleFingerprint: string;
} {
  if (typeof window === "undefined") {
    return { schedule: [], report: null, scheduleFingerprint: "" };
  }

  try {
    const raw = window.sessionStorage.getItem(PEDAGOGICAL_CACHE_KEY);
    if (!raw) {
      return { schedule: [], report: null, scheduleFingerprint: "" };
    }

    const parsed = JSON.parse(raw) as {
      schedule?: SessionSlot[];
      report?: unknown;
      scheduleFingerprint?: string;
    };

    const schedule = Array.isArray(parsed.schedule) ? parsed.schedule : [];
    return {
      schedule,
      report: parsed.report ?? null,
      scheduleFingerprint: parsed.scheduleFingerprint ?? fingerprintSchedule(schedule),
    };
  } catch {
    return { schedule: [], report: null, scheduleFingerprint: "" };
  }
}

// ← ADDED: worst-first ordering for the "issues" side of KeyFindings.
const SEVERITY_RANK: Record<CriterionResult["severity"], number> = { high: 0, medium: 1, low: 2 };


export default function PedagogicalAuditPage() {
  const location = useLocation();
  const cachedAudit = readCachedAudit();
  const navState = location.state as {
    preloadedSchedule?: SessionSlot[];
    preloadedConstraints?: Constraints | null;
  } | null;
  const preloadedSchedule = Array.isArray(navState?.preloadedSchedule)
    ? navState.preloadedSchedule
    : cachedAudit.schedule;
  const autoAuditStarted = useRef(false);

  const currentFingerprint = useMemo(
    () => fingerprintSchedule(preloadedSchedule),
    [preloadedSchedule],
  );
  const cacheMatchesCurrentSchedule =
    !!cachedAudit.report && cachedAudit.scheduleFingerprint === currentFingerprint;

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
    hydrateReport,
    reset,
  } = usePedagogicalAudit();

  // ── Local UI state ─────────────────────────────────────────────────────────
  const [selected, setSelected] = useState<CriterionResult | null>(null);
  const [activeSection, setActiveSection] = useState("pedagogical-overview");
  // ← ADDED: full criteria table is collapsed by default — it's the
  //   technical appendix, not the headline. Keeps the page short.
  const [showAllCriteria, setShowAllCriteria] = useState(false);

  useEffect(() => {
    if (cacheMatchesCurrentSchedule && !hasReport) {
      hydrateReport(cachedAudit.report as never);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheMatchesCurrentSchedule, cachedAudit.report, hasReport, hydrateReport]);

  useEffect(() => {
    if (hasReport || status !== "idle" || preloadedSchedule.length === 0 || autoAuditStarted.current) {
      return;
    }

    autoAuditStarted.current = true;
    void runAudit({
      schedule: preloadedSchedule,
    });
  }, [hasReport, preloadedSchedule, runAudit, status]);

  useEffect(() => {
    if (!report) {
      return;
    }

    try {
      window.sessionStorage.setItem(
        PEDAGOGICAL_CACHE_KEY,
        JSON.stringify({
          schedule: preloadedSchedule,
          report,
          scheduleFingerprint: currentFingerprint,
        }),
      );
    } catch {
      // Ignore storage failures and keep the page functional.
    }
  }, [preloadedSchedule, report, currentFingerprint]);

  useEffect(() => {
    const sectionIds = ["pedagogical-overview", "pedagogical-findings", "pedagogical-actions", "pedagogical-details"];
    const sections = sectionIds
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => Boolean(section));
    if (!sections.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActiveSection(visible.target.id);
      },
      { rootMargin: "-18% 0px -62% 0px", threshold: [0.1, 0.35, 0.7] },
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [hasReport]);

  // ── Handler: audit cached report or run from preloaded schedule ───────────
  const handleAudit = () => {
    setSelected(null);
    if (report?.planning_id != null && cacheMatchesCurrentSchedule) {
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

  // ← ADDED: split the backend's `recommendations` array. The backend
  //   (agents/pedagogical_agent.py, node_build_report) always builds it as
  //   `[explanation_paragraph, ...concrete_action_items]`, so index 0 is
  //   the human-readable narrative and the rest are the actionable items.
  //   This is a convention, not a typed field — if you want it
  //   bullet-proof, add a dedicated `explanation: str` field to
  //   AuditReport on the backend instead of relying on array position.
  const narrative   = report?.recommendations?.[0] ?? "";
  const actionItems = report?.recommendations?.slice(1) ?? [];

  // ← ADDED: curated "what's good / what needs fixing" instead of the old
  //   full session-by-session grid. Issues sorted worst-severity-first so
  //   the admin sees what matters most, first.
  const topIssues = [...failedCriteria].sort(
    (a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity],
  );


  // ── RENDER ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50">

      {/* ── Page header bar ─────────────────────────────────────────────── */}
      <div className="ped-page-top border-b border-slate-200 bg-white/90 backdrop-blur-sm">
        <div className="mx-auto max-w-6xl px-6 py-4">
          <div className="flex items-center gap-4">
            <div className="ped-page-icon flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-700 shadow-sm">
              <ClipboardCheck className="h-5 w-5" aria-hidden="true" />
            </div>

            <div className="min-w-0 flex-1">
              <h1 className="text-lg font-semibold tracking-tight text-slate-900">Pedagogical Report</h1>
              <p className="text-xs text-slate-500">
                Audit based on ISO 21001:2018 · ISO 29993:2017
              </p>
            </div>

          </div>
        </div>
      </div>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main className="mx-auto max-w-6xl px-6 py-8 space-y-6">

        {/* Error banner */}
        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800">
            {error}
          </div>
        )}

        {/* ── AUDIT HEADER ─── always visible */}
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

        <nav className="pedagogical-nav" aria-label="Audit sections">
          <span className="pedagogical-nav-label">Report sections</span>
          <div className="pedagogical-nav-links">
            {["Overview", "Findings", "Action plan", "Details"].map((label, index) => {
              const id = ["pedagogical-overview", "pedagogical-findings", "pedagogical-actions", "pedagogical-details"][index];
              return (
                <a
                  key={id}
                  href={`#${id}`}
                  className={activeSection === id ? "is-active" : ""}
                  onClick={() => setActiveSection(id)}
                >
                  {label}
                </a>
              );
            })}
          </div>
        </nav>

        {/* Loading state */}
        {isLoading && (
          <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-sm">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full
                            border-4 border-slate-200 border-t-slate-800" />
            <p className="text-sm font-semibold text-slate-700">
              Running pedagogical audit…
            </p>
          </div>
        )}

        {/* ── RESULTS — shown after successful audit ──────────────────────── */}
        {hasReport && report && !isLoading && (
          <>
            {/* ── Verdict: score gauge + AI narrative side by side ── */}
            <div id="pedagogical-overview" className="grid scroll-mt-28 gap-6 lg:grid-cols-2">
              <AuditScore
                score          = {report.score}
                grade          = {report.grade}
                isCompliant    = {report.is_compliant}
                complianceRate = {report.compliance_rate}
                highViolations = {report.high_violations}
              />
              <NarrativeSummary
                narrative   = {narrative}
                isCompliant = {report.is_compliant}
              />
            </div>

            {/* ── Key numbers ── */}
            <AuditSummary
              totalCriteria  = {report.total_criteria}
              passedCriteria = {report.passed_criteria}
              failedCriteria = {report.failed_criteria}
              highViolations = {report.high_violations}
              totalSessions  = {report.total_sessions}
              totalHours     = {report.total_hours}
            />

            {/* ── What's good / what needs fixing — curated, not everything ── */}
            <div id="pedagogical-findings" className="scroll-mt-28">
              <KeyFindings
                strengths = {passedCriteria}
                issues    = {topIssues}
                onSelect  = {setSelected}
              />
            </div>

            {/* ── Concrete action plan (narrative excluded, see above) ── */}
            <div id="pedagogical-actions" className="scroll-mt-28">
              {selected ? (
                <CriterionCard
                  criterion = {selected}
                  onClose   = {() => setSelected(null)}
                />
              ) : (
                <RecommendationList recommendations={actionItems} />
              )}
            </div>

            {/* ── Full criteria table — collapsed by default ── */}
            <div id="pedagogical-details" className="scroll-mt-28 rounded-3xl border border-slate-200 bg-white p-1 shadow-sm">
              <button
                type="button"
                onClick={() => setShowAllCriteria(v => !v)}
                className="flex w-full items-center justify-between rounded-[22px] px-5 py-4 text-left transition hover:bg-slate-50"
              >
                <span className="text-sm font-semibold text-slate-700">
                  View the full details of the {report.total_criteria} audited criteria
                </span>
                <span className="text-xs font-medium text-slate-400">
                  {showAllCriteria ? "Hide ▲" : "Show ▼"}
                </span>
              </button>
              {showAllCriteria && (
                <div className="border-t border-slate-100">
                  <CriteriaTable
                    criteria          = {allCriteria}
                    onSelectCriterion = {setSelected}
                    selectedRule      = {selected?.rule ?? null}
                  />
                </div>
              )}
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