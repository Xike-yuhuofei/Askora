import NoticeModal from './components/NoticeModal'
import AppShell from './components/AppShell'
import LearningShell from './components/LearningShell'
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
import Learning from './pages/Learning'
import Settings from './pages/Settings'
import RecoveryCenter from './pages/RecoveryCenter'
import Unavailable from './pages/Unavailable'
import Welcome from './pages/Welcome'
import { Navigate, useLocation } from './router'

const legacyRedirects = {
  '/': '/today',
  '/profile': '/learning/progress',
  '/knowledge': '/library',
  '/goals': '/learning/goals',
  '/path': '/learning/plan',
  '/evidence': '/learning/progress',
  '/history': '/learning/history',
}

const standardPages = {
  '/welcome': Welcome,
  '/today': Today,
  '/library': Library,
  '/learning': Learning,
  '/learning/goals': Goals,
  '/learning/plan': LearningPath,
  '/learning/progress': Evidence,
  '/learning/history': History,
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

const learningShellPaths = new Set([
  '/learning/goals',
  '/learning/plan',
  '/learning/progress',
  '/learning/history',
])

export function resolveRoute(pathname) {
  if (legacyRedirects[pathname]) return { type: 'redirect', to: legacyRedirects[pathname] }
  if (standardPages[pathname]) {
    const shell = learningShellPaths.has(pathname) ? 'learning' : 'standard'
    return { type: 'page', Page: standardPages[pathname], shell }
  }
  const quickMatch = pathname.match(/^\/quick\/([^/]+)$/)
  if (quickMatch) {
    return {
      type: 'workspace',
      sessionId: decodeRouteParam(quickMatch[1]),
      shell: 'workspace',
    }
  }

  if (pathname === '/goals/new') return { type: 'redirect', to: '/learning/goals', shell: 'standard' }
  if (pathname === '/learning/goals/new') return { type: 'goal-editor', shell: 'learning' }
  const goalDraftMatch = pathname.match(/^\/learning\/goals\/drafts\/([^/]+)$/)
  if (goalDraftMatch) return { type: 'goal-editor', draftId: decodeRouteParam(goalDraftMatch[1]), shell: 'learning' }
  const goalEditMatch = pathname.match(/^\/learning\/goals\/([^/]+)\/edit$/)
  if (goalEditMatch) return { type: 'goal-editor', editGoalId: decodeRouteParam(goalEditMatch[1]), shell: 'learning' }
  const goalDetailMatch = pathname.match(/^\/learning\/goals\/([^/]+)$/)
  if (goalDetailMatch) return { type: 'goal-detail', goalId: decodeRouteParam(goalDetailMatch[1]), shell: 'learning' }

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

  const route = resolveRoute(pathname)
  if (route.type === 'redirect') return <Navigate to={route.to} replace />

  let content
  if (route.type === 'page') content = <route.Page />
  else if (route.type === 'workspace') content = <TutorWorkspace sessionId={route.sessionId} />
  else if (route.type === 'book-learning') content = <BookLearningLaunch documentId={route.documentId} />
  else if (route.type === 'activity-learning') content = <ActivityLearning activityId={route.activityId} />
  else if (route.type === 'goal-editor') content = <GoalEditor draftId={route.draftId} editGoalId={route.editGoalId} />
  else if (route.type === 'goal-detail') content = <GoalDetail goalId={route.goalId} />
  else content = <Unavailable kind="not-found" />

  let wrappedContent = content
  if (route.shell === 'learning') {
    wrappedContent = <LearningShell>{content}</LearningShell>
  }

  return (
    <AppShell variant={route.shell}>
      {wrappedContent}
    </AppShell>
  )
}

export default function App() {
  return (
    <>
      <AppRoutes />
      <NoticeModal />
    </>
  )
}
