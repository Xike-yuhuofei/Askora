import { AuthProvider } from './hooks/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import NoticeModal from './components/NoticeModal'
import AppShell from './components/AppShell'
import Login from './pages/Login'
import Today from './pages/Today'
import TutorWorkspace from './pages/TutorWorkspace'
import History from './pages/History'
import Library from './pages/Library'
import BookLearningLaunch from './pages/BookLearningLaunch'
import ActivityLearning from './pages/ActivityLearning'
import Evidence from './pages/Evidence'
import Goals from './pages/Goals'
import GoalDetail from './pages/GoalDetail'
import GoalEditor from './pages/GoalEditor'
import LearningPath from './pages/LearningPath'
import Settings from './pages/Settings'
import RecoveryCenter from './pages/RecoveryCenter'
import AccountDeletion from './pages/AccountDeletion'
import Unavailable from './pages/Unavailable'
import Welcome from './pages/Welcome'
import { Navigate, useLocation } from './router'

const legacyRedirects = {
  '/': '/today',
  '/profile': '/evidence',
  '/knowledge': '/library',
  '/account': '/settings',
}

const standardPages = {
  '/welcome': Welcome,
  '/today': Today,
  '/library': Library,
  '/goals': Goals,
  '/path': LearningPath,
  '/evidence': Evidence,
  '/history': History,
  '/settings': Settings,
  '/settings/recovery': RecoveryCenter,
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
  const quickMatch = pathname.match(/^\/quick\/([^/]+)$/)
  if (quickMatch) {
    return {
      type: 'workspace',
      sessionId: decodeRouteParam(quickMatch[1]),
      shell: 'workspace',
    }
  }

  if (pathname === '/goals/new') return { type: 'goal-editor', shell: 'standard' }
  const goalDraftMatch = pathname.match(/^\/goals\/drafts\/([^/]+)$/)
  if (goalDraftMatch) return { type: 'goal-editor', draftId: decodeRouteParam(goalDraftMatch[1]), shell: 'standard' }
  const goalEditMatch = pathname.match(/^\/goals\/([^/]+)\/edit$/)
  if (goalEditMatch) return { type: 'goal-editor', editGoalId: decodeRouteParam(goalEditMatch[1]), shell: 'standard' }
  const goalDetailMatch = pathname.match(/^\/goals\/([^/]+)$/)
  if (goalDetailMatch) return { type: 'goal-detail', goalId: decodeRouteParam(goalDetailMatch[1]), shell: 'standard' }

  const activityMatch = pathname.match(/^\/learn\/([^/]+)$/)
  if (activityMatch) {
    return {
      type: 'activity-learning',
      activityId: decodeRouteParam(activityMatch[1]),
      shell: 'workspace',
    }
  }
  const bookLearningMatch = pathname.match(/^\/book-learning\/([^/]+)$/)
  if (bookLearningMatch) {
    return {
      type: 'book-learning',
      documentId: decodeRouteParam(bookLearningMatch[1]),
      shell: 'standard',
    }
  }
  return { type: 'not-found', shell: 'standard' }
}

function AppRoutes() {
  const { pathname } = useLocation()
  if (pathname === '/login') return <Login />
  if (pathname === '/settings/delete-account') return <AccountDeletion />

  const route = resolveRoute(pathname)
  if (route.type === 'redirect') return <Navigate to={route.to} replace />

  let content
  if (route.type === 'page') content = <route.Page />
  else if (route.type === 'workspace') content = <TutorWorkspace sessionId={route.sessionId} />
  else if (route.type === 'book-learning') content = <BookLearningLaunch documentId={route.documentId} />
  else if (route.type === 'activity-learning') content = <ActivityLearning activityId={route.activityId} />
  else if (route.type === 'goal-editor') content = <GoalEditor draftId={route.draftId} editGoalId={route.editGoalId} />
  else if (route.type === 'goal-detail') content = <GoalDetail goalId={route.goalId} />
  else if (route.type === 'unavailable') content = <Unavailable kind={route.kind} />
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
