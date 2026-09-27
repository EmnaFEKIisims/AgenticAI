// src/pages/admin/TrainersPage.tsx
import { useState } from "react";
import { GraduationCap } from "lucide-react";
import { useCrud } from "../../hooks/useCrud";
import { getTrainers, createTrainer, updateTrainer, deleteTrainer } from "../../services/crudServices";
import DataTable, { Column } from "../../components/crud/DataTable";
import SearchBar              from "../../components/crud/SearchBar";
import FormModal              from "../../components/crud/FormModal";
import DeleteDialog           from "../../components/crud/DeleteDialog";
import { EmptyState } from "../../components/crud/EmptyState";
import { LoadingState } from "../../components/crud/LoadingState";
import { Pagination } from "../../components/crud/Pagination";
import { AdminPageLayout, Field, ModalFooter, inputCls } from "./RoomsPage";
import type { Trainer } from "../../types/crud_types";

const EMPTY: Partial<Trainer> = { name: "", email: "", specialization: "", availability_notes: "" };

export default function TrainersPage() {
  const crud = useCrud<Trainer>(getTrainers, createTrainer, updateTrainer, deleteTrainer, ["name","email","specialization"]);
  const [modal,    setModal]    = useState<"none"|"add"|"edit">("none");
  const [delTarget,setDelTarget]= useState<Trainer | null>(null);
  const [form,     setForm]     = useState<Partial<Trainer>>(EMPTY);

  const openAdd  = () => { setForm(EMPTY); setModal("add"); };
  const openEdit = (t: Trainer) => { setForm(t); setModal("edit"); };
  const close    = () => setModal("none");

  const handleSave = async () => {
    if (modal === "add")  await crud.onCreate(form);
    if (modal === "edit") await crud.onUpdate(form.id!, form);
    close();
  };

  const columns: Column<Trainer>[] = [
    { key: "id",                 label: "ID",                 width: "60px" },
    { key: "name",               label: "Name" },
    { key: "email",              label: "Email" },
    { key: "specialization",     label: "Specialization" },
    { key: "availability_notes", label: "Availability" },
  ];

  return (
    <AdminPageLayout title="Trainers" icon={<GraduationCap className="h-7 w-7 text-slate-700" aria-hidden="true" />} total={crud.items.length}
      onAdd={openAdd} error={crud.error}
      search={<SearchBar value={crud.search} onChange={crud.setSearch} placeholder="Search trainers..." />}>

      {crud.isLoading && <LoadingState />}
      {!crud.isLoading && crud.filtered.length === 0 && <EmptyState message="No trainers found." onAdd={openAdd} />}
      {!crud.isLoading && crud.filtered.length > 0 && (
        <>
          <DataTable columns={columns} data={crud.filtered} rowKey="id" onEdit={openEdit} onDelete={setDelTarget} />
          <Pagination page={crud.page} total={crud.total} pageSize={10} onChange={crud.setPage} />
        </>
      )}

      {modal !== "none" && (
        <FormModal title={modal === "add" ? "Add Trainer" : "Edit Trainer"} onClose={close}>
          <Field label="Name">
            <input value={form.name ?? ""} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className={inputCls} />
          </Field>
          <Field label="Email">
            <input type="email" value={form.email ?? ""} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className={inputCls} />
          </Field>
          <Field label="Specialization">
            <input value={form.specialization ?? ""} onChange={e => setForm(f => ({ ...f, specialization: e.target.value }))} className={inputCls} placeholder="Python, Web Dev, Data Science..." />
          </Field>
          <Field label="Availability notes">
            <textarea value={form.availability_notes ?? ""} onChange={e => setForm(f => ({ ...f, availability_notes: e.target.value }))} className={inputCls} rows={3} />
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