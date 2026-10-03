// pages/AnomalyPage.tsx
// ================================
// Auto-loads all anomalies on mount — no planning ID input needed.
//
// FIX: component imports now match the ACTUAL folder casing
// (components/anomaly/... lowercase, not components/Anomaly/...) — this was
// silently breaking on case-sensitive filesystems (Linux CI/deploy) even
// though it may have worked on Windows dev machines.
//
// This file lives flat at src/pages/AnomalyPage.tsx (one level above
// components/), matching its own "../" import depth — NOT nested under
// pages/anomaly/.

import { useEffect }    from "react";
import { SearchCheck } from "lucide-react";
import { useAnomalies } from "../hooks/useAnomalies";
import AnomalyHeader from "../components/Anomaly/AnomalyHeader";
import AnomalySummary   from "../components/Anomaly/AnomalySummary";
import AnomalyFilters   from "../components/Anomaly/AnomalyFilters";
import AnomalyList      from "../components/Anomaly/AnomalyList";
import AnomalyDetails   from "../components/Anomaly/AnomalyDetails";
import "../styles/anomaly.css";


export default function AnomalyPage() {
  const {
    anomalies, selected, suggestions,
    isLoading, isLoadingSuggestions, error,
    filterSeverity, filterStatus, search,
    setFilterSeverity, setFilterStatus, setSearch,
    loadAllAnomalies, selectAnomaly,
    acknowledge, resolve, ignore,
    loadSuggestions,
  } = useAnomalies();

  // ── Auto-load all anomalies on page mount ─────────────────────────────────
  useEffect(() => {
    void loadAllAnomalies();
  }, [loadAllAnomalies]);

  const hasCritical = anomalies.some(a => a.severity === "high" && a.status === "open");
  const openCount   = anomalies.filter(a => a.status === "open").length;

  const handleSelect = (anomaly: typeof anomalies[0]) => {
    selectAnomaly(anomaly);
    if (anomaly.status === "open") {
      loadSuggestions(anomaly.id, []);
    }
  };

  return (
    <div className="anomaly-page min-h-screen bg-slate-50">

      {/* Top bar */}
      <div className="anomaly-topbar border-b border-slate-200 bg-white/90 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-4">
          <div className="anomaly-topbar-icon flex h-11 w-11 items-center justify-center rounded-xl border border-sky-100 bg-sky-50 text-sky-700 shadow-sm">
            <SearchCheck className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-semibold tracking-tight text-slate-900">Anomaly Agent</h1>
            <p className="text-xs text-slate-500">Detect · Classify · Resolve</p>
          </div>
        </div>
      </div>

      <main className="anomaly-main mx-auto max-w-6xl space-y-6 px-6 py-8">

        {/* Error */}
        {error && (
          <div className="anomaly-error rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800">
            {error}
          </div>
        )}

        {/* Header — status only, no input */}
        <AnomalyHeader
          totalAnomalies = {anomalies.length}
          openCount      = {openCount}
          hasCritical    = {hasCritical}
          isLoading      = {isLoading}
        />

        {/* Loading spinner */}
        {isLoading && (
          <div className="anomaly-loading rounded-3xl border border-slate-200 bg-white p-10 text-center">
            <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-800" />
            <p className="text-sm font-semibold text-slate-700">Loading anomalies…</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && anomalies.length === 0 && (
          <div className="anomaly-empty rounded-3xl border border-emerald-200 bg-emerald-50 p-10 text-center">
            <p className="text-sm font-semibold text-emerald-800">No anomalies detected.</p>
          </div>
        )}

        {/* Results */}
        {!isLoading && anomalies.length > 0 && (
          <>
            <AnomalySummary anomalies={anomalies} />

            <AnomalyFilters
              filterSeverity   = {filterSeverity}
              filterStatus     = {filterStatus}
              search           = {search}
              onSeverityChange = {setFilterSeverity}
              onStatusChange   = {setFilterStatus}
              onSearchChange   = {setSearch}
            />

            <div className="anomaly-results-grid grid gap-6 lg:grid-cols-[1fr_420px]">
              <AnomalyList
                anomalies      = {anomalies}
                selected       = {selected}
                filterSeverity = {filterSeverity}
                filterStatus   = {filterStatus}
                search         = {search}
                onSelect       = {handleSelect}
                onAcknowledge  = {acknowledge}
                onResolve      = {resolve}
                onIgnore       = {ignore}
              />

              {selected && (
                <AnomalyDetails
                  anomaly              = {selected}
                  suggestions          = {suggestions}
                  isLoadingSuggestions = {isLoadingSuggestions}
                  onClose              = {() => selectAnomaly(null)}
                  onAcknowledge        = {acknowledge}
                  onResolve            = {resolve}
                  onIgnore             = {ignore}
                />
              )}
            </div>
          </>
        )}

      </main>
    </div>
  );
}