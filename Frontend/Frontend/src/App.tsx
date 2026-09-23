import { useEffect, useState } from 'react'
import { ArrowLeft, Moon, Sun, UserRound } from 'lucide-react'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import DataPage from './pages/Data.js'
import ConstraintPage from './pages/Constraint.js'
import PlanningPage from './pages/Planning.js'
import StartPage from './pages/Start.js'
import PedagogicalPage from './pages/Pedagogical.js'
import AnomalyPage from './pages/AnomalyPage.js'
import RagPage from './pages/RagPage.js'
import UserPage from './pages/UserPage.js'
import NotificationsPage from './pages/NotificationsPage.js'
import RoomsPage from './pages/CRUD/RoomsPage.js'
import TrainersPage      from "./pages/CRUD/TrainersPage";
import LearnerGroupsPage from "./pages/CRUD/LearnerGroupsPage";
import CoursesPage       from "./pages/CRUD/CoursesPage";
import EquipmentPage     from "./pages/CRUD/EquipmentPage";
import CrudPage from './pages/CRUD/CrudPage.js'

function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const [theme, setTheme] = useState<'cupcake' | 'synthwave'>('cupcake')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((current) => (current === 'cupcake' ? 'synthwave' : 'cupcake'))
  }

  const nextThemeLabel =
    theme === 'cupcake' ? 'Passer en mode sombre' : 'Retour en mode clair'

  const goToUserPage = () => {
    navigate('/user')
  }

  const isStartPage = location.pathname === '/'

  return (
    <div className="app-shell">
      {!isStartPage && (
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="back-btn"
          aria-label="Go back"
          title="Go back"
        >
          <ArrowLeft className="theme-icon" strokeWidth={2.25} aria-hidden="true" />
        </button>
      )}

      <div className="top-actions">
        <div className="theme-toggle-wrapper" data-tooltip={nextThemeLabel}>
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={nextThemeLabel}
          >
            {theme === 'cupcake' ? (
              <Moon className="theme-icon" strokeWidth={2.25} aria-hidden="true" />
            ) : (
              <Sun className="theme-icon" strokeWidth={2.25} aria-hidden="true" />
            )}
          </button>
        </div>

        <button
          type="button"
          onClick={goToUserPage}
          className="icon-top-btn user-top-btn"
          aria-label="Open user profile"
          title="User profile"
        >
          <UserRound className="theme-icon" strokeWidth={2.25} aria-hidden="true" />
        </button>

      </div>

      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/constraints" element={<ConstraintPage />} />
        <Route path="/planning" element={<PlanningPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/pedagogical-audit" element={<PedagogicalPage  />} />
        <Route path="/anomaly" element={<AnomalyPage />} />
        <Route path="/anomaly/*" element={<AnomalyPage />} />
        <Route path="/rag" element={<RagPage />} />
        <Route path="/user" element={<UserPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/crud" element={<CrudPage />} />
        <Route path="/admin/rooms"          element={<RoomsPage />} />
        <Route path="/admin/trainers"       element={<TrainersPage />} />
        <Route path="/admin/learner-groups" element={<LearnerGroupsPage />} />
        <Route path="/admin/courses"        element={<CoursesPage />} />
        <Route path="/admin/equipment"      element={<EquipmentPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App
