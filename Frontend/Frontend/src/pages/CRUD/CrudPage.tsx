import { ArrowRight, BookOpen, Building2, GraduationCap, HardHat, Users } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const resources = [
  { label: 'Courses', description: 'Manage the courses used in planning.', icon: BookOpen, path: '/admin/courses' },
  { label: 'Equipment', description: 'Manage available equipment and quantities.', icon: HardHat, path: '/admin/equipment' },
  { label: 'Learner Groups', description: 'Manage learner groups and levels.', icon: Users, path: '/admin/learner-groups' },
  { label: 'Rooms', description: 'Manage rooms, types, and capacities.', icon: Building2, path: '/admin/rooms' },
  { label: 'Trainers', description: 'Manage trainers and specializations.', icon: GraduationCap, path: '/admin/trainers' },
]

export default function CrudPage() {
  const navigate = useNavigate()

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12">
      <section className="mx-auto max-w-5xl">
        <header className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Data management</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">What would you like to manage?</h1>
          <p className="mt-2 text-slate-600">Choose a resource to create, edit, search, or delete its records.</p>
        </header>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {resources.map(({ label, description, icon: Icon, path }) => (
            <button
              key={path}
              type="button"
              onClick={() => navigate(path)}
              className="group flex min-h-40 flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md"
            >
              <span className="flex items-start justify-between">
                <Icon className="text-slate-700" size={25} aria-hidden="true" />
                <ArrowRight className="text-slate-400 transition group-hover:translate-x-1 group-hover:text-slate-700" size={20} aria-hidden="true" />
              </span>
              <span>
                <span className="block text-lg font-semibold text-slate-900">{label}</span>
                <span className="mt-1 block text-sm text-slate-500">{description}</span>
              </span>
            </button>
          ))}
        </div>
      </section>
    </main>
  )
}