// src/pages/admin/CoursesPage.tsx
import { useState } from "react";
import { BookOpen } from "lucide-react";
import { useCrud } from "../../hooks/useCrud";
import { getCourses, createCourse, updateCourse, deleteCourse } from "../../services/crudServices";
import DataTable, { Column } from "../../components/crud/DataTable";
import SearchBar              from "../../components/crud/SearchBar";
import FormModal              from "../../components/crud/FormModal";
import DeleteDialog           from "../../components/crud/DeleteDialog";
import { EmptyState } from "../../components/crud/EmptyState";
import { LoadingState } from "../../components/crud/LoadingState";
import { Pagination } from "../../components/crud/Pagination";
import { AdminPageLayout, Field, ModalFooter, inputCls } from "./RoomsPage";
import type { Course } from "../../types/crud_types";

const EMPTY: Partial<Course> = { title:"", description:"", total_hours: 30, session_duration: 180, pedagogical_objectives:"" };

export default function CoursesPage() {
  const crud = useCrud<Course>(getCourses, createCourse, updateCourse, deleteCourse, ["title","description"]);
  const [modal,    setModal]    = useState<"none"|"add"|"edit">("none");
  const [delTarget,setDelTarget]= useState<Course | null>(null);
  const [form,     setForm]     = useState<Partial<Course>>(EMPTY);

  const openAdd  = () => { setForm(EMPTY); setModal("add"); };
  const openEdit = (c: Course) => { setForm(c); setModal("edit"); };
  const close    = () => setModal("none");

  const handleSave = async () => {
    if (modal === "add")  await crud.onCreate(form);
    if (modal === "edit") await crud.onUpdate(form.id!, form);
    close();
  };

  const columns: Column<Course>[] = [
    { key: "id",              label: "ID",       width: "60px" },
    { key: "title",           label: "Title" },
    { key: "total_hours",     label: "Hours",    render: c => `${c.total_hours}h` },
    { key: "session_duration",label: "Session",  render: c => `${c.session_duration} min` },
    { key: "is_active",       label: "Status",   render: c => c.is_active
        ? <span className="text-xs font-semibold text-emerald-700">Active</span>
        : <span className="text-xs font-semibold text-rose-600">Inactive</span> },
  ];

  return (
    <AdminPageLayout title="Courses" icon={<BookOpen className="h-7 w-7 text-slate-700" aria-hidden="true" />} total={crud.items.length}
      onAdd={openAdd} error={crud.error}
      search={<SearchBar value={crud.search} onChange={crud.setSearch} placeholder="Search courses..." />}>
      {crud.isLoading && <LoadingState />}
      {!crud.isLoading && crud.filtered.length === 0 && <EmptyState message="No courses found." onAdd={openAdd} />}
      {!crud.isLoading && crud.filtered.length > 0 && (
        <>
          <DataTable columns={columns} data={crud.filtered} rowKey="id" onEdit={openEdit} onDelete={setDelTarget} />
          <Pagination page={crud.page} total={crud.total} pageSize={10} onChange={crud.setPage} />
        </>
      )}
      {modal !== "none" && (
        <FormModal title={modal === "add" ? "Add Course" : "Edit Course"} onClose={close}>
          <Field label="Title">
            <input value={form.title ?? ""} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} className={inputCls} placeholder="Python Programming" />
          </Field>
          <Field label="Description">
            <textarea value={form.description ?? ""} rows={2}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              className={`${inputCls} resize-none`} />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Total hours">
              <input type="number" min={1} value={form.total_hours ?? 30}
                onChange={e => setForm(f => ({ ...f, total_hours: +e.target.value }))} className={inputCls} />
            </Field>
            <Field label="Session duration (min)">
              <input type="number" min={60} value={form.session_duration ?? 180}
                onChange={e => setForm(f => ({ ...f, session_duration: +e.target.value }))} className={inputCls} />
            </Field>
          </div>
          <Field label="Pedagogical objectives">
            <textarea value={form.pedagogical_objectives ?? ""} rows={3}
              onChange={e => setForm(f => ({ ...f, pedagogical_objectives: e.target.value }))}
              className={`${inputCls} resize-none`} placeholder="Understand Python basics, data types..." />
          </Field>
          <ModalFooter onCancel={close} onSave={handleSave} saving={crud.saving} />
        </FormModal>
      )}
      {delTarget && (
        <DeleteDialog name={delTarget.title} loading={crud.deleting}
          onConfirm={async () => { await crud.onDelete(delTarget.id); setDelTarget(null); }}
          onCancel={() => setDelTarget(null)} />
      )}
    </AdminPageLayout>
  );
}