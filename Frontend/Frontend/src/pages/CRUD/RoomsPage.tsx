// src/pages/admin/RoomsPage.tsx
import { useState } from "react";
import { useCrud }     from "../../hooks/useCrud";
import { getRooms, createRoom, updateRoom, deleteRoom } from "../../services/crudServices";
import DataTable, { Column } from "../../components/crud/DataTable";
import SearchBar              from "../../components/crud/SearchBar";
import FormModal              from "../../components/crud/FormModal";
import DeleteDialog           from "../../components/crud/DeleteDialog";
import { EmptyState }         from "../../components/crud/EmptyState";
import { LoadingState }       from "../../components/crud/EmptyState";
import { Pagination }         from "../../components/crud/EmptyState";
import type { Room }          from "../../types/crud_types";
import { useNavigate } from "react-router-dom";

const CRUD_LINKS = [
  ["Courses", "/admin/courses"],
  ["Equipment", "/admin/equipment"],
  ["Learner Groups", "/admin/learner-groups"],
  ["Rooms", "/admin/rooms"],
  ["Trainers", "/admin/trainers"],
] as const;

const ROOM_TYPES = ["classroom","lab","conference","amphitheater"];

const EMPTY: Partial<Room> = { name: "", room_type: "classroom", capacity: 20 };

export default function RoomsPage() {
  const crud = useCrud<Room>(getRooms, createRoom, updateRoom, deleteRoom, ["name","room_type"]);
  const [modal,    setModal]    = useState<"none"|"add"|"edit">("none");
  const [delTarget,setDelTarget]= useState<Room | null>(null);
  const [form,     setForm]     = useState<Partial<Room>>(EMPTY);

  const openAdd  = () => { setForm(EMPTY); setModal("add"); };
  const openEdit = (r: Room) => { setForm(r); setModal("edit"); };
  const close    = () => setModal("none");

  const handleSave = async () => {
    if (modal === "add")  await crud.onCreate(form);
    if (modal === "edit") await crud.onUpdate(form.id!, form);
    close();
  };

  const columns: Column<Room>[] = [
    { key: "id",        label: "ID",       width: "60px" },
    { key: "name",      label: "Name" },
    { key: "room_type", label: "Type",   render: r => <span className="rounded-lg bg-slate-100 px-2 py-0.5 text-xs font-medium">{r.room_type}</span> },
    { key: "capacity",  label: "Capacity", render: r => `${r.capacity} seats` },
    { key: "is_active", label: "Status",   render: r => r.is_active
        ? <span className="text-xs font-semibold text-emerald-700">Active</span>
        : <span className="text-xs font-semibold text-rose-600">Inactive</span> },
  ];

  return (
    <AdminPageLayout title="Rooms" icon="🏫" total={crud.items.length}
      onAdd={openAdd} error={crud.error}
      search={<SearchBar value={crud.search} onChange={crud.setSearch} placeholder="Search rooms..." />}>

      {crud.isLoading  && <LoadingState />}
      {!crud.isLoading && crud.filtered.length === 0 && <EmptyState message="No rooms found." onAdd={openAdd} />}
      {!crud.isLoading && crud.filtered.length > 0 && (
        <>
          <DataTable columns={columns} data={crud.filtered} rowKey="id"
            onEdit={openEdit} onDelete={setDelTarget} />
          <Pagination page={crud.page} total={crud.total} pageSize={10} onChange={crud.setPage} />
        </>
      )}

      {modal !== "none" && (
        <FormModal title={modal === "add" ? "Add Room" : "Edit Room"} onClose={close}>
          <Field label="Name">
            <input value={form.name ?? ""} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className={inputCls} placeholder="Conference C301" />
          </Field>
          <Field label="Type">
            <select value={form.room_type ?? "classroom"} onChange={e => setForm(f => ({ ...f, room_type: e.target.value }))}
              className={inputCls}>
              {ROOM_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Capacity">
            <input type="number" min={1} value={form.capacity ?? 20}
              onChange={e => setForm(f => ({ ...f, capacity: +e.target.value }))}
              className={inputCls} />
          </Field>
          <ModalFooter onCancel={close} onSave={handleSave} saving={crud.saving} />
        </FormModal>
      )}

      {delTarget && (
        <DeleteDialog name={delTarget.name} loading={crud.deleting}
          onConfirm={async () => { await crud.onDelete(delTarget.id); setDelTarget(null); }}
          onCancel={() => setDelTarget(null)} />
      )}
    </AdminPageLayout>
  );
}

// ── Shared layout helpers ──────────────────────────────────────────────────────

export function AdminPageLayout({ title, icon, total, onAdd, error, search, children }: {
  title: string; icon: string; total: number; onAdd: () => void;
  error: string | null; search: React.ReactNode; children: React.ReactNode;
}) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="border-b border-slate-200 bg-white px-6 py-5">
        <div className="mx-auto max-w-5xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <div>
              <h1 className="text-xl font-bold text-slate-900">{title}</h1>
              <p className="text-xs text-slate-500">{total} item(s)</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {search}
            <button onClick={onAdd}
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 transition">
              + Add
            </button>
          </div>
        </div>
        <nav className="mx-auto mt-4 flex max-w-5xl flex-wrap gap-2" aria-label="CRUD resources">
          {CRUD_LINKS.map(([label, path]) => (
            <button key={path} type="button" onClick={() => navigate(path)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${path.endsWith(title.toLowerCase().replace(" ", "-")) ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
              {label}
            </button>
          ))}
        </nav>
      </div>
      <main className="mx-auto max-w-5xl px-6 py-6">
        {error && (
          <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            ❌ {error}
          </div>
        )}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          {children}
        </div>
      </main>
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-semibold text-slate-600">{label}</label>
      {children}
    </div>
  );
}

export function ModalFooter({ onCancel, onSave, saving }: { onCancel: () => void; onSave: () => void; saving: boolean }) {
  return (
    <div className="flex gap-3 pt-2">
      <button onClick={onCancel} className="flex-1 rounded-xl border border-slate-200 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
      <button onClick={onSave} disabled={saving} className="flex-1 rounded-xl bg-slate-900 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60">
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}

export const inputCls = "w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none focus:border-slate-400 focus:bg-white transition";