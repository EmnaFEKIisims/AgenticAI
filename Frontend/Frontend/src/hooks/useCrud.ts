// src/hooks/useCrud.ts
// ONE generic hook reused by ALL entity pages.
// Usage: const rooms = useCrud(getRooms, createRoom, updateRoom, deleteRoom);

import { useState, useEffect, useCallback } from "react";

interface CrudHookReturn<T> {
  items:      T[];
  isLoading:  boolean;
  error:      string | null;
  search:     string;
  page:       number;
  filtered:   T[];
  total:      number;
  setSearch:  (v: string) => void;
  setPage:    (p: number) => void;
  refresh:    () => Promise<void>;
  onCreate:   (data: Partial<T>) => Promise<void>;
  onUpdate:   (id: number, data: Partial<T>) => Promise<void>;
  onDelete:   (id: number) => Promise<void>;
  saving:     boolean;
  deleting:   boolean;
}

const PAGE_SIZE = 10;

export function useCrud<T extends { id: number; [k: string]: any }>(
  fetchFn:  () => Promise<T[]>,
  createFn: (data: any) => Promise<T>,
  updateFn: (id: number, data: any) => Promise<T>,
  deleteFn: (id: number) => Promise<any>,
  searchKeys: (keyof T)[] = [],
): CrudHookReturn<T> {
  const [items,    setItems]    = useState<T[]>([]);
  const [isLoading,setIsLoading]= useState(false);
  const [error,    setError]    = useState<string | null>(null);
  const [search,   setSearch]   = useState("");
  const [page,     setPage]     = useState(1);
  const [saving,   setSaving]   = useState(false);
  const [deleting, setDeleting] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true); setError(null);
    try { setItems(await fetchFn()); }
    catch (e) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setIsLoading(false); }
  }, [fetchFn]);

  useEffect(() => { void refresh(); }, [refresh]);

  const filtered = items.filter(item => {
    if (!search) return true;
    const q = search.toLowerCase();
    return searchKeys.some(k => String(item[k] ?? "").toLowerCase().includes(q));
  });

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const onCreate = useCallback(async (data: Partial<T>) => {
    setSaving(true); setError(null);
    try { await createFn(data); await refresh(); setPage(1); }
    catch (e) { setError(e instanceof Error ? e.message : "Create failed"); throw e; }
    finally { setSaving(false); }
  }, [createFn, refresh]);

  const onUpdate = useCallback(async (id: number, data: Partial<T>) => {
    setSaving(true); setError(null);
    try { await updateFn(id, data); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Update failed"); throw e; }
    finally { setSaving(false); }
  }, [updateFn, refresh]);

  const onDelete = useCallback(async (id: number) => {
    setDeleting(true); setError(null);
    try { await deleteFn(id); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Delete failed"); throw e; }
    finally { setDeleting(false); }
  }, [deleteFn, refresh]);

  return {
    items, isLoading, error, search, page,
    filtered: paginated, total: filtered.length,
    setSearch: (v) => { setSearch(v); setPage(1); },
    setPage,
    refresh, onCreate, onUpdate, onDelete,
    saving, deleting,
  };
}