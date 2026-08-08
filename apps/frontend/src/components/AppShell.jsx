import Sidebar from './Sidebar'
import './AppShell.css'

export default function AppShell({ children, variant = 'standard' }) {
  return (
    <div className={`app-shell app-shell--${variant}`}>
      <Sidebar />
      <main className={`app-main app-main--${variant}`} id="main-content">
        {children}
      </main>
    </div>
  )
}
