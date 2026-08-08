import { AuthProvider } from './hooks/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import NoticeModal from './components/NoticeModal'
import AppShell from './components/AppShell'
import Login from './pages/Login'
import Today from './pages/Today'
import TutorWorkspace from './pages/TutorWorkspace'
import History from './pages/History'
import Library from './pages/Library'
import Settings from './pages/Settings'
import Unavailable from './pages/Unavailable'
import { Navigate, useLocation } from './router'

const legacyRedirects = {
  '/': '/today',
  '/profile': '/evidence',
  '/knowledge': '/library',
  '/account': '/settings',
}

const standardPages = {
  '/today': Today,
  '/library': Library,
  '/history': History,
  '/settings': Settings,
}

const unavailablePages = {
  '/goals': 'goals',
  '/path': 'path',
  '/evidence': 'evidence',
}

function decodeRouteParam(value) {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

export function resolveRoute(pathname) {
  if (legacyRedirects[pathname]) return { type: 'redirect', to: legacyRedirects[pathname] }
  if (standardPages[pathname]) return { type: 'page', Page: standardPages[pathname], shell: 'standard' }
  if (unavailablePages[pathname]) {
    return { type: 'unavailable', kind: unavailablePages[pathname], shell: 'standard' }
  }

  const quickMatch = pathname.match(/^\/quick\/([^/]+)$/)
  if (quickMatch) {
    return {
      type: 'workspace',
      sessionId: decodeRouteParam(quickMatch[1]),
      shell: 'workspace',
    }
  }

  const activityMatch = pathname.match(/^\/learn\/([^/]+)$/)
  if (activityMatch) {
    return {
      type: 'activity-unavailable',
      activityId: decodeRouteParam(activityMatch[1]),
      shell: 'workspace',
    }
  }
  return { type: 'not-found', shell: 'standard' }
}

function AppRoutes() {
  const { pathname } = useLocation()
  if (pathname === '/login') return <Login />

  const route = resolveRoute(pathname)
  if (route.type === 'redirect') return <Navigate to={route.to} replace />

  let content
  if (route.type === 'page') content = <route.Page />
  else if (route.type === 'workspace') content = <TutorWorkspace sessionId={route.sessionId} />
  else if (route.type === 'activity-unavailable') {
    content = <Unavailable kind="activity" resourceId={route.activityId} />
  } else if (route.type === 'unavailable') content = <Unavailable kind={route.kind} />
  else content = <Unavailable kind="not-found" />

  return (
    <ProtectedRoute>
      <AppShell variant={route.shell}>{content}</AppShell>
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
