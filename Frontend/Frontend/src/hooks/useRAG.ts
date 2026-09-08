// src/hooks/useRAG.ts

import { useState, useCallback }        from "react";
import type { RAGContextResponse, KnowledgeDocument } from "../types/rag";
import {
  getPlanningContext, getConstraintContext, getPedagogicalContext,
  listDocuments, ingestDocument, seedPedagogicalRules,
} from "../services/ragService";

interface UseRAGReturn {
  context:     RAGContextResponse | null;
  documents:   KnowledgeDocument[];
  isLoading:   boolean;
  error:       string | null;
  fetchPlanningContext:    (userId: string) => Promise<RAGContextResponse | null>;
  fetchConstraintContext:  (userId: string) => Promise<RAGContextResponse | null>;
  fetchPedagogicalContext: (userId: string) => Promise<RAGContextResponse | null>;
  loadDocuments:           () => Promise<void>;
  onIngestDocument: (title: string, source: string, content: string) => Promise<void>;
  onSeedRules:      (userId: string) => Promise<void>;
}

export function useRAG(): UseRAGReturn {
  const [context,   setContext]   = useState<RAGContextResponse | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  const wrap = async <T>(fn: () => Promise<T>): Promise<T | null> => {
    setIsLoading(true); setError(null);
    try { return await fn(); }
    catch (e) { setError(e instanceof Error ? e.message : "Error"); return null; }
    finally { setIsLoading(false); }
  };

  const fetchPlanningContext = useCallback(async (userId: string) => {
    const r = await wrap(() => getPlanningContext(userId));
    if (r) setContext(r);
    return r;
  }, []);

  const fetchConstraintContext = useCallback(async (userId: string) => {
    const r = await wrap(() => getConstraintContext(userId));
    if (r) setContext(r);
    return r;
  }, []);

  const fetchPedagogicalContext = useCallback(async (userId: string) => {
    const r = await wrap(() => getPedagogicalContext(userId));
    if (r) setContext(r);
    return r;
  }, []);

  const loadDocuments = useCallback(async () => {
    const r = await wrap(() => listDocuments());
    if (r) setDocuments(r.documents);
  }, []);

  const onIngestDocument = useCallback(async (title: string, source: string, content: string) => {
    await wrap(() => ingestDocument({ title, source, document_type: "pedagogical_guide", content }));
    await loadDocuments();
  }, [loadDocuments]);

  const onSeedRules = useCallback(async (userId: string) => {
    await wrap(() => seedPedagogicalRules(userId));
  }, []);

  return {
    context, documents, isLoading, error,
    fetchPlanningContext, fetchConstraintContext, fetchPedagogicalContext,
    loadDocuments, onIngestDocument, onSeedRules,
  };
}