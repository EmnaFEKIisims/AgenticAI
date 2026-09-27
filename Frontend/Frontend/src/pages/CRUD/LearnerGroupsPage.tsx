// src/pages/admin/LearnerGroupsPage.tsx
import { useState } from "react";
import { UsersRound } from "lucide-react";
import { useCrud } from "../../hooks/useCrud";
import { getGroups, createGroup, updateGroup, deleteGroup } from "../../services/crudServices";
import DataTable, { Column } from "../../components/crud/DataTable";
import SearchBar              from "../../components/crud/SearchBar";
import FormModal              from "../../components/crud/FormModal";
import DeleteDialog           from "../../components/crud/DeleteDialog";
import { EmptyState } from "../../components/crud/EmptyState";
import { LoadingState } from "../../components/crud/LoadingState";
import { Pagination } from "../../components/crud/Pagination";
import { AdminPageLayout, Field, ModalFooter, inputCls } from "./RoomsPage";
import type { LearnerGroup } from "../../types/crud_types";

const LEVELS = ["beginner","intermediate","advanced"];
const EMPTY: Partial<LearnerGroup> = { name:"", size: 20, level: "intermediate" };

export default function LearnerGroupsPage() {
  const crud = useCrud<LearnerGroup>(getGroups, createGroup, updateGroup, deleteGroup, ["name","level"]);
  const [modal,    setModal]    = useState<"none"|"add"|"edit">("none");
  const [delTarget,setDelTarget]= useState<LearnerGroup | null>(null);
  const [form,     setForm]     = useState<Partial<LearnerGroup>>(EMPTY);

  const openAdd  = () => { setForm(EMPTY); setModal("add"); };
  const openEdit = (g: LearnerGroup) => { setForm(g); setModal("edit"); };
  const close    = () => setModal("none");

  const handleSave = async () => {
    if (modal === "add")  await crud.onCreate(form);
    if (modal === "edit") await crud.onUpdate(form.id!, form);
    close();
  };

  const columns: Column<LearnerGroup>[] = [
    { key: "id",        label: "ID",    width: "60px" },
    { key: "name",      label: "Name" },
    { key: "size",      label: "Size",  render: g => `${g.size} learners` },
    { key: "level",     label: "Level", render: g =>
        <span className={`rounded-lg px-2 py-0.5 text-xs font-medium ${
          g.level === "advanced" ? "bg-violet-100 text-violet-700" :
          g.level === "intermediate" ? "bg-sky-100 text-sky-700" : "bg-emerald-100 text-emerald-700"
        }`}>{g.level ?? "—"}</span> },
    { key: "is_active", label: "Status", render: g => g.is_active
        ? <span className="text-xs font-semibold text-emerald-700">Active</span>
        : <span className="text-xs font-semibold text-rose-600">Inactive</span> },
  ];

  return (
    <AdminPageLayout title="Learner Groups" icon={<UsersRound className="h-7 w-7 text-slate-700" aria-hidden="true" />} total={crud.items.length}
      onAdd={openAdd} error={crud.error}
      search={<SearchBar value={crud.search} onChange={crud.setSearch} placeholder="Search groups..." />}>
      {crud.isLoading && <LoadingState />}
      {!crud.isLoading && crud.filtered.length === 0 && <EmptyState message="No groups found." onAdd={openAdd} />}
      {!crud.isLoading && crud.filtered.length > 0 && (
        <>
          <DataTable columns={columns} data={crud.filtered} rowKey="id" onEdit={openEdit} onDelete={setDelTarget} />
          <Pagination page={crud.page} total={crud.total} pageSize={10} onChange={crud.setPage} />
        </>
      )}
      {modal !== "none" && (
        <FormModal title={modal === "add" ? "Add Group" : "Edit Group"} onClose={close}>
          <Field label="Group Name">
            <input value={form.name ?? ""} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className={inputCls} placeholder="Group Data Science 1" />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Size (learners)">
              <input type="number" min={1} value={form.size ?? 20} onChange={e => setForm(f => ({ ...f, size: +e.target.value }))} className={inputCls} />
            </Field>
            <Field label="Level">
              <select value={form.level ?? "intermediate"} onChange={e => setForm(f => ({ ...f, level: e.target.value }))} className={inputCls}>
                {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </Field>
          </div>
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