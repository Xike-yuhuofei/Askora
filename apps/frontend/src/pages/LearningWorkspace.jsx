import { useEffect, useRef, useState } from 'react'
import { BookOpen } from 'lucide-react'
import * as workspaceApi from '../api/workspace'
import { useWorkspace } from '../components/WorkspaceContext'
import Alert from '../components/ui/Alert'
import { useNavigate } from '../router'
import './LearningWorkspace.css'

// LW-07：对话状态（进行中 / 可开始），非仅颜色（A-02）。
function conversationStatus(item) {
  if (item.launch_state === 'RESUMABLE' || item.status === 'active') return '进行中'
  return '可开始'
}

export default function LearningWorkspace({ workspaceId }) {
  const navigate = useNavigate()
  const workspace = useWorkspace()
  const current = workspace?.current_workspace
  const spaceId = workspaceId || current?.workspace_id
  const displayName = current?.workspace_id === spaceId ? current.display_name : '空间'
  const [activities, setActivities] = useState({ status: spaceId ? 'loading' : 'empty', items: [] })
  const [continueError, setContinueError] = useState('')
  const [continuing, setContinuing] = useState(false)
  const headingRef = useRef(null)

  useEffect(() => {
    if (!spaceId) {
      setActivities({ status: 'empty', items: [] })
      return undefined
    }
    let cancelled = false
    setActivities({ status: 'loading', items: [] })
    workspaceApi.listWorkspaceActivities(spaceId)
      .then((payload) => {
        if (cancelled) return
        setActivities({
          status: payload?.data?.view_state === 'EMPTY' ? 'empty' : 'ready',
          items: payload?.data?.activities || [],
        })
      })
      .catch(() => {
        if (!cancelled) setActivities({ status: 'error', items: [] })
      })
    return () => { cancelled = true }
  }, [spaceId])

  // LW-03 / A-03：切换空间后重新解析，focus 落到空间 h1（语义起点）。
  useEffect(() => {
    if (spaceId && headingRef.current) headingRef.current.focus()
  }, [spaceId])

  const openable = activities.items.filter((item) => (
    item.launch_state === 'RESUMABLE' || ['active', 'available'].includes(item.status)
  ))
  const startable = activities.items.find((item) => (
    item.launch_state === 'REQUIRES_START_COMMAND' && item.status === 'available'
  ))

  const continueLearning = async () => {
    if (!startable || continuing) return
    const activityId = workspaceApi.parseActivityId(startable.activity_ref)
    if (!activityId) {
      setContinueError('没有可启动的学习活动。')
      return
    }
    setContinuing(true)
    setContinueError('')
    try {
      const lifecycle = await workspaceApi.getActivityLifecycle(activityId)
      if (!lifecycle?.data?.execution?.can_start) {
        setContinueError('现在还不能开始有依据的学习。')
        return
      }
      await workspaceApi.startActivity(activityId, {
        schema_version: '1.0',
        activity_id: activityId,
        expected_state_version: lifecycle.data.state.version,
        idempotency_key: globalThis.crypto?.randomUUID?.() || `start-${Date.now()}`,
      })
      const href = workspaceApi.conversationHref(spaceId, startable.activity_ref)
      if (href) navigate(href)
    } catch {
      setContinueError('继续学习失败，不会从前端创建对话。')
    } finally {
      setContinuing(false)
    }
  }

  // LW-03：当前空间名状态（LOADING / EMPTY / READY / PARTIAL / STALE / ERROR）。
  let workspaceLabel = '还没有当前空间'
  if (spaceId) {
    if (workspace?.status === 'loading') workspaceLabel = '加载中…'
    else if (workspace?.status === 'error') workspaceLabel = '暂时不可用'
    else if (workspace?.status === 'partial') workspaceLabel = '部分信息可用'
    else if (workspace?.status === 'stale') workspaceLabel = '信息可能已过期'
    else workspaceLabel = displayName
  }

  // LW-04：无可启动活动时，继续学习按钮 disabled 并说明。
  const showDisabledReason = !startable && activities.status !== 'loading' && activities.status !== 'error'

  return (
    <div className="learning-canvas" data-workspace-id={spaceId}>
      <header className="learning-canvas__header">
        <div className="learning-canvas__title">
          <p className="eyebrow">空间</p>
          <h1 tabIndex={-1} ref={headingRef}>空间</h1>
          <span className="learning-canvas__workspace" data-workspace-state={workspace?.status}>
            {workspaceLabel}
          </span>
        </div>
      </header>

      <section className="learning-canvas__continue" aria-label="继续学习">
        <button
          type="button"
          className="button button--primary"
          onClick={continueLearning}
          disabled={continuing || !startable}
        >
          {continuing ? '正在继续…' : '继续学习'}
        </button>
        {/* LW-05：在该空间新开一段对话，接续学习进度。 */}
        <p className="learning-canvas__continue-hint">在该空间新开一段对话，接续学习进度。</p>
        {showDisabledReason && !continueError && (
          <p className="learning-canvas__continue-reason">当前没有可启动的学习活动，无法从此处继续学习。</p>
        )}
      </section>

      <section className="learning-canvas__empty" aria-labelledby="learning-canvas-empty-title">
        <BookOpen size={28} aria-hidden="true" />
        <h2 id="learning-canvas-empty-title">
          {activities.status === 'loading' ? '正在读取对话…' : (openable.length ? '打开一段已有对话' : '这是一个空空间')}
        </h2>
        {/* LW-08：对话列表 LOADING 态，加载中不提前渲染空态。 */}
        {activities.status === 'loading' && (
          <p>正在读取对话…</p>
        )}
        {activities.status === 'error' && (
          <Alert role="alert" tone="danger" title="对话列表暂时无法读取">
            不会从前端生成占位对话。
          </Alert>
        )}
        {continueError && <Alert role="alert" tone="danger" title="无法继续学习">{continueError}</Alert>}
        {activities.status !== 'error' && activities.status !== 'loading' && openable.length === 0 && !startable && (
          <>
            <p>可以加入资料，但现在还不能开始有依据的学习。打开此页不会创建对话。</p>
            <Alert role="alert" tone="info" title="当前没有可恢复的对话">
              对空间「继续学习」需要 SYS06 已经给出可启动的活动，本页不会自行开聊。
            </Alert>
          </>
        )}
        {openable.length > 0 && (
          <ul className="learning-canvas__conversations">
            {openable.map((item) => {
              const href = workspaceApi.conversationHref(spaceId, item.activity_ref)
              return (
                <li key={item.activity_ref}>
                  <button
                    type="button"
                    className="button button--secondary learning-canvas__conversation"
                    onClick={() => href && navigate(href)}
                  >
                    <span className="learning-canvas__conversation-title">{item.display_title}</span>
                    <span className="learning-canvas__conversation-status">{conversationStatus(item)}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </section>
    </div>
  )
}