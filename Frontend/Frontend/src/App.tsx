import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Navigate, Route, Routes } from 'react-router-dom'
import DataPage from './pages/Data.js'
import ConstraintPage from './pages/Constraint.js'
import PlanningPage from './pages/Planning.js'
import StartPage from './pages/Start.js'
import PedagogicalPage from './pages/Pedagogical.js'
import AnomalyPage from './pages/AnomalyPage.js'

function App() {
  const [theme, setTheme] = useState<'cupcake' | 'synthwave'>('cupcake')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((current) => (current === 'cupcake' ? 'synthwave' : 'cupcake'))
  }

  const nextThemeLabel =
    theme === 'cupcake' ? 'Passer en mode sombre' : 'Retour en mode clair'

  return (
    <div className="app-shell">
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

      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/constraints" element={<ConstraintPage />} />
        <Route path="/planning" element={<PlanningPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/pedagogical-audit" element={<PedagogicalPage  />} />
        <Route path="/anomaly" element={<AnomalyPage />} />
        <Route path="/anomaly/*" element={<AnomalyPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App
