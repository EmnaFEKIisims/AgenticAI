import {
  ArrowRight,
  Database,
  FileUp,
  Settings2,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function StartPage() {
  const navigate = useNavigate()

  return (
    <main className="relative min-h-[calc(100vh-4rem)] overflow-hidden px-4 py-10 sm:px-8 lg:px-12">
      <div className="pointer-events-none absolute -left-32 -top-32 h-80 w-80 rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-24 h-96 w-96 rounded-full bg-secondary/10 blur-3xl" />

      <section className="relative mx-auto flex w-full max-w-6xl flex-col justify-center">
        <header className="mx-auto max-w-3xl text-center">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary">
            <Sparkles size={16} aria-hidden="true" />
            <span>Your planning workspace</span>
          </div>
          <h1 className="text-4xl font-black tracking-tight text-base-content sm:text-5xl lg:text-6xl">
            Build better schedules,
            <span className="block text-primary">starting here.</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-base-content/65 sm:text-lg">
            Welcome back. Set up your data, define your rules, and keep every planning decision
            in one clear workspace.
          </p>
        </header>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          <button
            type="button"
            onClick={() => navigate('/data')}
            className="group relative flex min-h-72 flex-col overflow-hidden rounded-3xl border border-base-300/70 bg-base-100 p-7 text-left shadow-sm transition duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/10 focus:outline-none focus:ring-4 focus:ring-primary/20"
          >
            <div className="mb-8 flex items-start justify-between">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary transition group-hover:bg-primary group-hover:text-primary-content">
                <FileUp size={23} aria-hidden="true" />
              </div>
              <span className="rounded-full bg-base-200 px-3 py-1 text-xs font-bold uppercase tracking-wider text-base-content/50">
                Step 01
              </span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-base-content">Upload your data</h2>
            <p className="mt-3 flex-1 text-sm leading-6 text-base-content/65">
              Bring in your CSV, Excel, or PDF files and review everything before you start.
            </p>
            <span className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-primary">
              Import files
              <ArrowRight size={17} className="transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/constraints')}
            className="group relative flex min-h-72 flex-col overflow-hidden rounded-3xl border border-base-300/70 bg-base-100 p-7 text-left shadow-sm transition duration-300 hover:-translate-y-1 hover:border-secondary/40 hover:shadow-xl hover:shadow-secondary/10 focus:outline-none focus:ring-4 focus:ring-secondary/20"
          >
            <div className="mb-8 flex items-start justify-between">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary/10 text-secondary transition group-hover:bg-secondary group-hover:text-secondary-content">
                <Database size={23} aria-hidden="true" />
              </div>
              <span className="rounded-full bg-base-200 px-3 py-1 text-xs font-bold uppercase tracking-wider text-base-content/50">
                Step 02
              </span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-base-content">Define constraints</h2>
            <p className="mt-3 flex-1 text-sm leading-6 text-base-content/65">
              Set the rules and preferences that make your generated schedule truly yours.
            </p>
            <span className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-secondary">
              Configure rules
              <ArrowRight size={17} className="transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/crud')}
            className="group relative flex min-h-72 flex-col overflow-hidden rounded-3xl border border-base-300/70 bg-base-100 p-7 text-left shadow-sm transition duration-300 hover:-translate-y-1 hover:border-accent/40 hover:shadow-xl hover:shadow-accent/10 focus:outline-none focus:ring-4 focus:ring-accent/20"
          >
            <div className="mb-8 flex items-start justify-between">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent transition group-hover:bg-accent group-hover:text-accent-content">
                <Settings2 size={23} aria-hidden="true" />
              </div>
              <span className="rounded-full bg-base-200 px-3 py-1 text-xs font-bold uppercase tracking-wider text-base-content/50">
                Anytime
              </span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-base-content">Manage workspace</h2>
            <p className="mt-3 flex-1 text-sm leading-6 text-base-content/65">
              Keep courses, rooms, trainers, equipment, and learner groups up to date.
            </p>
            <span className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-accent">
              Open data manager
              <ArrowRight size={17} className="transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </button>
        </div>

        <footer className="mx-auto mt-10 flex flex-wrap items-center justify-center gap-x-7 gap-y-3 text-sm text-base-content/55">
          <span className="inline-flex items-center gap-2">
            <ShieldCheck size={17} className="text-success" aria-hidden="true" />
            Your workflow, your control
          </span>
          <span className="hidden h-1 w-1 rounded-full bg-base-content/30 sm:block" />
          <span>Start with any step and adjust later</span>
        </footer>
      </section>
    </main>
  )
}
