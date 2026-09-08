// src/pages/admin/EquipmentPage.tsx
import { useState } from "react";
import { useCrud } from "../../hooks/useCrud";
import { getEquipments, createEquipment, updateEquipment, deleteEquipment } from "../../services/crudServices";
import DataTable, { Column } from "../../components/crud/DataTable";
import SearchBar              from "../../components/crud/SearchBar";
import FormModal              from "../../components/crud/FormModal";
import DeleteDialog           from "../../components/crud/DeleteDialog";
import { EmptyState, LoadingState, Pagination } from "../../components/crud/EmptyState";
import { AdminPageLayout, Field, ModalFooter, inputCls } from "./RoomsPage";
import type { Equipment } from "../../types/crud_types";

const EMPTY: Partial<Equipment> = { name:"", equipment_type:"", quantity: 1 };

export default function EquipmentPage() {
  const crud = useCrud<Equipment>(getEquipments, createEquipment, updateEquipment, deleteEquipment, ["name","equipment_type"]);
  const [modal,    setModal]    = useState<"none"|"add"|"edit">("none");
  const [delTarget,setDelTarget]= useState<Equipment | null>(null);
  const [form,     setForm]     = useState<Partial<Equipment>>(EMPTY);

  const openAdd  = () => { setForm(EMPTY); setModal("add"); };
  const openEdit = (e: Equipment) => { setForm(e); setModal("edit"); };
  const close    = () => setModal("none");

  const handleSave = async () => {
    if (modal === "add")  await crud.onCreate(form);
    if (modal === "edit") await crud.onUpdate(form.id!, form);
    close();
  };

  const columns: Column<Equipment>[] = [
    { key: "id",             label: "ID",       width: "60px" },
    { key: "name",           label: "Name" },
    { key: "equipment_type", label: "Type",     render: e => <span className="rounded-lg bg-slate-100 px-2 py-0.5 text-xs">{e.equipment_type}</span> },
    { key: "quantity",       label: "Quantity" },
    { key: "is_available",   label: "Status",   render: e => e.is_available
        ? <span className="text-xs font-semibold text-emerald-700">Available</span>
        : <span className="text-xs font-semibold text-rose-600">Unavailable</span> },
  ];

  return (
    <AdminPageLayout title="Equipment" icon="🔧" total={crud.items.length}
      onAdd={openAdd} error={crud.error}
      search={<SearchBar value={crud.search} onChange={crud.setSearch} placeholder="Search equipment..." />}>
      {crud.isLoading && <LoadingState />}
      {!crud.isLoading && crud.filtered.length === 0 && <EmptyState message="No equipment found." onAdd={openAdd} />}
      {!crud.isLoading && crud.filtered.length > 0 && (
        <>
          <DataTable columns={columns} data={crud.filtered} rowKey="id" onEdit={openEdit} onDelete={setDelTarget} />
          <Pagination page={crud.page} total={crud.total} pageSize={10} onChange={crud.setPage} />
        </>
      )}
      {modal !== "none" && (
        <FormModal title={modal === "add" ? "Add Equipment" : "Edit Equipment"} onClose={close}>
          <Field label="Name">
            <input value={form.name ?? ""} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className={inputCls} placeholder="Projector, Whiteboard..." />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Type">
              <input value={form.equipment_type ?? ""} onChange={e => setForm(f => ({ ...f, equipment_type: e.target.value }))} className={inputCls} placeholder="audio-visual, lab..." />
            </Field>
            <Field label="Quantity">
              <input type="number" min={1} value={form.quantity ?? 1} onChange={e => setForm(f => ({ ...f, quantity: +e.target.value }))} className={inputCls} />
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