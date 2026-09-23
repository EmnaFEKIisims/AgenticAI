// hooks/useAnomalies.ts
// FIX: interface had a typo "anommlies" instead of "anomalies" (line 13),
// while the rest of the file (useState, return statement) correctly used
// "anomalies" — that mismatch is what TS2561 was pointing at.

import { useState, useCallback } from "react";
import type { Anomaly, AnomalySeverity, AnomalyStatus, SuggestionsResponse } from "../types/anomaly";
import {
  getAllAnomalies,
  getAnomaliesByPlanning,
  updateAnomalyStatus,
  getAnomalySuggestions,
} from "../services/anomalyService";

interface UseAnomaliesReturn {
  anomalies:            Anomaly[];
  selected:             Anomaly | null;
  suggestions:          SuggestionsResponse | null;
  isLoading:            boolean;
  isLoadingSuggestions: boolean;
  error:                string | null;
  filterSeverity:       AnomalySeverity | "all";
  filterStatus:         AnomalyStatus   | "all";
  search:               string;
  setFilterSeverity:    (v: AnomalySeverity | "all") => void;
  setFilterStatus:      (v: AnomalyStatus   | "all") => void;
  setSearch:            (v: string) => void;
  loadAllAnomalies:     () => Promise<void>;           // ← loads ALL anomalies (no ID needed)
  loadAnomalies:        (planningId: number) => Promise<void>;
  selectAnomaly:        (a: Anomaly | null) => void;
  acknowledge:          (id: number) => Promise<void>;
  resolve:              (id: number) => Promise<void>;
  ignore:               (id: number) => Promise<void>;
  loadSuggestions:      (id: number, schedule: Record<string, unknown>[]) => Promise<void>;
  reset:                () => void;
}

export function useAnomalies(): UseAnomaliesReturn {
  const [anomalies,            setAnomalies]            = useState<Anomaly[]>([]);
  const [selected,             setSelected]             = useState<Anomaly | null>(null);
  const [suggestions,          setSuggestions]          = useState<SuggestionsResponse | null>(null);
  const [isLoading,            setIsLoading]            = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [error,                setError]                = useState<string | null>(null);
  const [filterSeverity,       setFilterSeverity]       = useState<AnomalySeverity | "all">("all");
  const [filterStatus,         setFilterStatus]         = useState<AnomalyStatus   | "all">("open");
  const [search,               setSearch]               = useState("");

  // ── Load ALL anomalies — called automatically on page mount ───────────────
  const loadAllAnomalies = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getAllAnomalies();
      setAnomalies(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load anomalies");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ── Load anomalies for a specific planning ID ─────────────────────────────
  const loadAnomalies = useCallback(async (planningId: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getAnomaliesByPlanning(planningId);
      setAnomalies(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load anomalies");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ── Status updates ────────────────────────────────────────────────────────
  const updateStatus = useCallback(async (
    anomalyId: number,
    status: "acknowledged" | "resolved" | "ignored",
  ) => {
    try {
      const updated = await updateAnomalyStatus(anomalyId, status);
      setAnomalies(prev => prev.map(a => a.id === anomalyId ? updated : a));
      if (selected?.id === anomalyId) setSelected(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Status update failed");
    }
  }, [selected]);

  const acknowledge = useCallback((id: number) => updateStatus(id, "acknowledged"), [updateStatus]);
  const resolve     = useCallback((id: number) => updateStatus(id, "resolved"),     [updateStatus]);
  const ignore      = useCallback((id: number) => updateStatus(id, "ignored"),      [updateStatus]);

  // ── Load suggestions ──────────────────────────────────────────────────────
  const loadSuggestions = useCallback(async (
    anomalyId: number,
    schedule:  Record<string, unknown>[],
  ) => {
    setIsLoadingSuggestions(true);
    try {
      const data = await getAnomalySuggestions(anomalyId, schedule);
      setSuggestions(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load suggestions");
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, []);

  const reset = useCallback(() => {
    setAnomalies([]); setSelected(null); setSuggestions(null);
    setError(null); setIsLoading(false);
    setFilterSeverity("all"); setFilterStatus("open"); setSearch("");
  }, []);

  return {
    anomalies, selected, suggestions,
    isLoading, isLoadingSuggestions, error,
    filterSeverity, filterStatus, search,
    setFilterSeverity, setFilterStatus, setSearch,
    loadAllAnomalies, loadAnomalies,
    selectAnomaly: setSelected,
    acknowledge, resolve, ignore,
    loadSuggestions, reset,
  };
}