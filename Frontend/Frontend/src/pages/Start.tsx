import { Database, Settings2, Upload } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function StartPage() {
  const navigate = useNavigate()

  return (
    <main className="min-h-[80vh] flex items-center justify-center px-4 py-10">
      <section className="w-full max-w-5xl">
        <header className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-base-content">Welcome</h1>
          <p className="mt-3 text-base md:text-lg text-base-content/70">
            Choose how you want to start your planning workflow.
          </p>
        </header>

        <div className="grid gap-5 md:grid-cols-3">
          <button
            type="button"
            onClick={() => navigate('/data')}
            className="rounded-2xl border border-base-300 bg-base-100 p-7 text-left shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition"
          >
            <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-blue-100 text-blue-700 mb-4">
              <Upload size={20} aria-hidden="true" />
            </div>
            <h2 className="text-2xl font-semibold text-base-content">Upload New Data</h2>
            <p className="mt-2 text-base-content/70">
              Import CSV, Excel, or PDF files, review extracted rows, fix issues, then validate.
            </p>
          </button>

          <button
            type="button"
            onClick={() => navigate('/constraints')}
            className="rounded-2xl border border-base-300 bg-base-100 p-7 text-left shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition"
          >
            <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 mb-4">
              <Database size={20} aria-hidden="true" />
            </div>
            <h2 className="text-2xl font-semibold text-base-content">Create Constraints</h2>
            <p className="mt-2 text-base-content/70">
              Open the constraint page first, then generate the planning schedule.
            </p>
          </button>

          <button
            type="button"
            onClick={() => navigate('/crud')}
            className="rounded-2xl border border-base-300 bg-base-100 p-7 text-left shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition"
          >
            <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-amber-100 text-amber-700 mb-4">
              <Settings2 size={20} aria-hidden="true" />
            </div>
            <h2 className="text-2xl font-semibold text-base-content">Manage Data</h2>
            <p className="mt-2 text-base-content/70">
              Create, update, search, and remove courses, rooms, trainers, equipment, and learner groups.
            </p>
          </button>
        </div>
      </section>
    </main>
  )
}
