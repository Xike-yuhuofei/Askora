import { AuthProvider } from './hooks/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import NoticeModal from './components/NoticeModal'
import Login from './pages/Login'
import Chat from './pages/Chat'
import Profile from './pages/Profile'
import Knowledge from './pages/Knowledge'
import Account from './pages/Account'
import { Navigate, useLocation } from './router'

const protectedPages = {
  '/': Chat,
  '/profile': Profile,
  '/knowledge': Knowledge,
  '/account': Account,
}

function AppRoutes() {
  const { pathname } = useLocation()
  if (pathname === '/login') return <Login />

  const Page = protectedPages[pathname]
  if (!Page) return <Navigate to="/" replace />
  return (
    <ProtectedRoute>
      <Page />
    </ProtectedRoute>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
      <NoticeModal />
    </AuthProvider>
  )
}
