// src/pages/admin/RoomsPage.tsx
import { useState } from "react";
import { AlertTriangle, Building2, Plus } from "lucide-react";
import { useCrud }     from "../../hooks/useCrud";
import { getRooms, createRoom, updateRoom, deleteRoom } from "../../services/crudServices";
import DataTable, { Column } from "../../components/crud/DataTable";
import SearchBar              from "../../components/crud/SearchBar";
import FormModal              from "../../components/crud/FormModal";
import DeleteDialog           from "../../components/crud/DeleteDialog";
import { EmptyState }         from "../../components/crud/EmptyState";
import { LoadingState }       from "../../components/crud/LoadingState";
import { Pagination }         from "../../components/crud/Pagination";
import type { Room }          from "../../types/crud_types";
import { useNavigate } from "react-router-dom";
import "../../styles/crud.css";

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
    <AdminPageLayout title="Rooms" icon={<Building2 className="h-7 w-7 text-slate-700" aria-hidden="true" />} total={crud.items.length}
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
  title: string; icon: React.ReactNode; total: number; onAdd: () => void;
  error: string | null; search: React.ReactNode; children: React.ReactNode;
}) {
  const navigate = useNavigate();
  const descriptions: Record<string, string> = {
    Rooms: "Spaces and capacity available for each session.",
    Trainers: "People, expertise, and availability for your planning.",
    "Learner Groups": "Cohorts, levels, and learner capacity.",
    Courses: "The learning catalogue used to build schedules.",
    Equipment: "Resources and quantities available to trainers.",
  };

  return (
    <div className="crud-page crud-entity-page">
      <header className="crud-entity-header">
        <div className="crud-entity-header-inner">
          <div className="crud-entity-heading">
            <span className="crud-entity-icon">{icon}</span>
            <div>
              <p className="crud-kicker">Workspace / Administration</p>
              <h1>{title}</h1>
              <p>{descriptions[title]}</p>
            </div>
          </div>
          <div className="crud-entity-actions">
            <span className="crud-record-count"><strong>{total}</strong> {total === 1 ? "record" : "records"}</span>
            {search}
            <button onClick={onAdd} className="crud-add-button">
              <Plus className="h-4 w-4" aria-hidden="true" />
              Add {title.replace(/s$/, "")}
            </button>
          </div>
        </div>
        <nav className="crud-resource-nav" aria-label="CRUD resources">
          {CRUD_LINKS.map(([label, path]) => (
            <button key={path} type="button" onClick={() => navigate(path)}
              className={`crud-nav-item ${path.endsWith(title.toLowerCase().replace(" ", "-")) ? "is-active" : ""}`}>
              {label}
            </button>
          ))}
        </nav>
      </header>
      <main className="crud-entity-main">
        {error && (
          <div className="crud-error">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
            {error}
          </div>
        )}
        <div className="crud-table-card">
          <div className="crud-table-card-header">
            <div>
              <span className="crud-section-label">Collection</span>
              <h2>{title} records</h2>
            </div>
            <span className="crud-table-card-note">Updated in your workspace</span>
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="crud-field">
      <label>{label}</label>
      {children}
    </div>
  );
}

export function ModalFooter({ onCancel, onSave, saving }: { onCancel: () => void; onSave: () => void; saving: boolean }) {
  return (
    <div className="crud-modal-footer">
      <button onClick={onCancel} className="crud-modal-cancel">Cancel</button>
      <button onClick={onSave} disabled={saving} className="crud-modal-save">
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}

export const inputCls = "crud-input";