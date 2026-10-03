import { ArrowUpRight, BookOpen, Building2, Check, Database, GraduationCap, HardHat, ShieldCheck, Users } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import '../../styles/crud.css'

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
    <main className="crud-page">
      <section className="crud-overview crud-hub">
        <div className="crud-hub-topline">
          <span><Building2 size={15} aria-hidden="true" /> ScheduleForge / Workspace</span>
          <span className="crud-overview-status"><i /> All systems ready</span>
        </div>

        <div className="crud-hub-hero">
          <div className="crud-hub-copy">
            <p className="crud-kicker">Data administration</p>
            <h1>The workspace behind your schedule.</h1>
            <p>Keep courses, people, rooms, and equipment aligned before you generate a plan.</p>
          </div>
          <aside className="crud-readiness-panel">
            <div className="crud-readiness-heading">
              <span><ShieldCheck size={16} aria-hidden="true" /> Planning readiness</span>
              <strong>100%</strong>
            </div>
            <div className="crud-readiness-track"><span /></div>
            <div className="crud-readiness-foot"><span>5 collections connected</span><span><Check size={13} /> Ready to plan</span></div>
          </aside>
        </div>

        <div className="crud-resource-heading">
          <div>
            <span className="crud-section-label">Your collections</span>
            <h2>Choose what to manage</h2>
          </div>
          <p>Each collection feeds directly into the planning engine.</p>
        </div>

        <div className="crud-resource-grid">
          {resources.map(({ label, description, icon: Icon, path }, index) => (
            <button key={path} type="button" onClick={() => navigate(path)} className={`crud-resource-card crud-resource-card-${index + 1}`}>
              <span className="crud-resource-top">
                <span className="crud-resource-index">0{index + 1}</span>
                <span className="crud-resource-icon"><Icon size={21} aria-hidden="true" /></span>
                <ArrowUpRight className="crud-resource-arrow" size={19} aria-hidden="true" />
              </span>
              <span className="crud-resource-copy"><span>{label}</span><small>{description}</small></span>
              <span className="crud-resource-link">Open collection <ArrowUpRight size={14} aria-hidden="true" /></span>
            </button>
          ))}
        </div>

        <footer className="crud-hub-footer"><Database size={14} aria-hidden="true" /> Changes here are reflected in your next generated planning.</footer>
      </section>
    </main>
  )
}