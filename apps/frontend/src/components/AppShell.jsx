import Sidebar from './Sidebar'
import RecoveryIndicator from './RecoveryIndicator'
import './AppShell.css'

export default function AppShell({ children, variant = 'standard' }) {
  return (
    <div className={`app-shell app-shell--${variant}`}>
      <Sidebar />
      <main className={`app-main app-main--${variant}`} id="main-content">
        <RecoveryIndicator />
        {children}
      </main>
    </div>
  )
}
