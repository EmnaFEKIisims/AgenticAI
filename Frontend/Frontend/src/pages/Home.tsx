import {
  ArrowRight,
  Database,
  FileUp,
  Gauge,
  Layers3,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
} from 'lucide-react'
import { login } from '../services/authService'

const capabilities = [
  {
    icon: FileUp,
    title: 'Bring your data together',
    description: 'Import the files that power your training and planning workflow in one place.',
    className: 'bg-primary/10 text-primary',
  },
  {
    icon: SlidersHorizontal,
    title: 'Turn rules into clarity',
    description: 'Describe your requirements and let the planning engine work with your priorities.',
    className: 'bg-blue-100 text-blue-700',
  },
  {
    icon: Database,
    title: 'Keep your workspace ready',
    description: 'Manage courses, rooms, trainers, equipment, and learner groups with confidence.',
    className: 'bg-rose-100 text-rose-700',
  },
]

export default function HomePage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-base-100 text-base-content">
      <div className="pointer-events-none absolute -left-40 -top-40 h-128 w-lg rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-48 -right-32 h-136 w-136 rounded-full bg-blue-100/60 blur-3xl" />

      <nav className="relative mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 sm:px-10 lg:px-12">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-content shadow-lg shadow-primary/20">
            <Sparkles size={20} aria-hidden="true" />
          </span>
          <div>
            <span className="block text-lg font-black tracking-tight">ScheduleForge</span>
            <span className="hidden text-xs font-medium text-base-content/50 sm:block">AI Planning Studio</span>
          </div>
        </div>
        <button
          type="button"
          onClick={login}
          className="inline-flex items-center gap-2 rounded-xl border border-base-300 bg-base-100 px-4 py-2.5 text-sm font-bold text-base-content shadow-sm transition hover:-translate-y-0.5 hover:border-primary/40 hover:text-primary hover:shadow-md focus:outline-none focus:ring-4 focus:ring-primary/20"
        >
          Sign in
          <ArrowRight size={16} aria-hidden="true" />
        </button>
      </nav>

      <section className="relative mx-auto grid w-full max-w-7xl items-center gap-14 px-6 pb-20 pt-12 sm:px-10 lg:grid-cols-[1.05fr_0.95fr] lg:px-12 lg:pb-28 lg:pt-20">
        <div className="max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-bold text-primary">
            <Sparkles size={16} aria-hidden="true" />
            <span>Planning that feels effortless</span>
          </div>
          <h1 className="text-5xl font-black leading-[1.02] tracking-[-0.04em] sm:text-6xl lg:text-7xl">
            Make every
            <span className="block text-primary">schedule smarter.</span>
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-base-content/65 sm:text-xl">
            ScheduleForge brings your data, constraints, and planning decisions together so your
            team can move from complexity to a clear, reliable schedule.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={login}
              className="group inline-flex items-center gap-3 rounded-2xl bg-primary px-6 py-3.5 text-base font-bold text-primary-content shadow-lg shadow-primary/25 transition hover:-translate-y-1 hover:shadow-xl hover:shadow-primary/30 focus:outline-none focus:ring-4 focus:ring-primary/25"
            >
              Start planning
              <ArrowRight size={19} className="transition-transform group-hover:translate-x-1" aria-hidden="true" />
            </button>
            <span className="inline-flex items-center gap-2 text-sm font-semibold text-base-content/55">
              <ShieldCheck size={18} className="text-success" aria-hidden="true" />
              Secure sign-in with Keycloak
            </span>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-md">
          <div className="absolute -inset-5 rounded-[2.5rem] bg-primary/10 blur-2xl" />
          <div className="relative overflow-hidden rounded-4xl border border-base-300/70 bg-base-100 p-6 shadow-2xl shadow-primary/10">
            <div className="flex items-center justify-between border-b border-base-200 pb-5">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-base-content/45">Your planning flow</p>
                <h2 className="mt-1 text-xl font-black">From input to impact</h2>
              </div>
              <div className="rounded-xl bg-success/10 p-2.5 text-success">
                <Gauge size={21} aria-hidden="true" />
              </div>
            </div>
            <div className="space-y-3 pt-5">
              {[
                ['01', 'Upload your data', FileUp, 'primary'],
                ['02', 'Define constraints', SlidersHorizontal, 'blue'],
                ['03', 'Generate your plan', Layers3, 'rose'],
              ].map(([number, label, Icon, color]) => (
                <div key={number} className="flex items-center gap-4 rounded-2xl border border-base-200 bg-base-200/40 p-4">
                  <span className="text-xs font-black text-base-content/35">{number}</span>
                  <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${color === 'primary' ? 'bg-primary/10 text-primary' : color === 'blue' ? 'bg-blue-100 text-blue-700' : 'bg-rose-100 text-rose-700'}`}>
                    <Icon size={18} aria-hidden="true" />
                  </span>
                  <span className="text-sm font-bold">{label}</span>
                  <ArrowRight size={16} className="ml-auto text-base-content/30" aria-hidden="true" />
                </div>
              ))}
            </div>
            <div className="mt-5 flex items-center gap-3 rounded-2xl bg-success/10 px-4 py-3 text-sm font-semibold text-success">
              <ShieldCheck size={18} aria-hidden="true" />
              <span>Ready when your team is</span>
            </div>
          </div>
        </div>
      </section>

      <section className="relative mx-auto w-full max-w-7xl border-t border-base-200 px-6 py-14 sm:px-10 lg:px-12 lg:py-20">
        <div className="mb-9 max-w-xl">
          <p className="text-sm font-black uppercase tracking-[0.18em] text-primary">One connected workspace</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Everything you need to plan with confidence.</h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {capabilities.map(({ icon: Icon, title, description, className }) => (
            <article key={title} className="rounded-3xl border border-base-300/70 bg-base-100 p-6 shadow-sm">
              <span className={`mb-6 flex h-12 w-12 items-center justify-center rounded-2xl ${className}`}>
                <Icon size={22} aria-hidden="true" />
              </span>
              <h3 className="text-xl font-bold">{title}</h3>
              <p className="mt-3 text-sm leading-6 text-base-content/60">{description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
