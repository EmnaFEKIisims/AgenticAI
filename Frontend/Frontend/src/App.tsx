import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Navigate, Route, Routes } from 'react-router-dom'
import PlanningPage from './pages/Planning'

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
        <Route path="/" element={<PlanningPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App
