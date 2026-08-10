import { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, ChevronRight, Loader2 } from 'lucide-react'

import * as onboardingApi from '../api/onboarding'
import { normalizeApiError } from '../api/client'
import { useNavigate } from '../router'
import './Welcome.css'

const STEP_LABELS = {
  MODEL: '模型',
  MATERIAL: '资料',
  GOAL: '目标',
  FIRST_ACTIVITY: '第一节',
}

const STATE_CLASS = {
  NOT_STARTED: 'step--pending',
  IN_PROGRESS: 'step--in-progress',
  COMPLETE: 'step--complete',
  BLOCKED: 'step--blocked',
  STALE: 'step--stale',
}

const STATE_LABEL = {
  NOT_STARTED: '待完成',
  IN_PROGRESS: '进行中',
  COMPLETE: '已完成',
  BLOCKED: '已阻塞',
  STALE: '已过期',
}

export default function Welcome() {
  const navigate = useNavigate()
  const [journey, setJourney] = useState(null)
  const [state, setState] = useState('loading') // loading | ready | error
  const [error, setError] = useState('')
  const [primaryLoading, setPrimaryLoading] = useState(false)
  const [dismissLoading, setDismissLoading] = useState(false)
  const [announcement, setAnnouncement] = useState('')
  const didMount = useRef(false)

  const loadJourney = useCallback(async () => {
    setState('loading')
    setError('')
    setAnnouncement('正在读取首次引导状态…')
    try {
      const data = await onboardingApi.getOnboardingJourney()
      setJourney(data)
      setState('ready')
      setAnnouncement(`当前状态 ${data.journey_state}`)
    } catch (err) {
      const info = normalizeApiError(err)
      setState('error')
      setError(info.message || '无法读取首次引导状态')
      setAnnouncement(`读取失败：${info.message || '未知错误'}`)
    }
  }, [])

  useEffect(() => {
    if (didMount.current) return
    didMount.current = true
    loadJourney()
  }, [loadJourney])

  const stepOrder = ['MODEL', 'MATERIAL', 'GOAL', 'FIRST_ACTIVITY']
  const steps = stepOrder.map((stepName) => {
    const found = journey?.steps?.find((item) => item.step === stepName)
    return found || {
      step: stepName,
      state: 'NOT_STARTED',
      title: STEP_LABELS[stepName],
      summary: '等待下一步',
      source_status: [],
    }
  })

  const nextAction = journey?.next_action || {
    action_code: 'NONE',
    kind: 'none',
    label: '暂不可用',
    enabled: false,
    route: null,
    recovery_action: null,
  }

  const boundaryAcknowledged = Boolean(journey?.boundary_notice?.acknowledged)

  const primaryAction = async () => {
    if (!nextAction.enabled) return
    setPrimaryLoading(true)
    setAnnouncement('正在执行主操作…')
    try {
      if (nextAction.action_code === 'ACKNOWLEDGE_BOUNDARIES') {
        const updated = await onboardingApi.acknowledgeBoundaries({
          expectedVersion: journey.preference.preference_version,
          noticeVersion: journey.boundary_notice.notice_version,
        })
        setJourney(updated)
        setAnnouncement('已确认数据与模型说明')
        return
      }
      if (nextAction.action_code === 'OPEN_TODAY') {
        navigate('/today')
        return
      }
      if (nextAction.action_code === 'OPEN_MODEL_SETTINGS') {
        navigate('/settings')
        return
      }
      if (nextAction.route) {
        navigate(nextAction.route)
        return
      }
    } catch (err) {
      const info = normalizeApiError(err)
      setError(info.message || '操作失败')
      setAnnouncement(`操作失败：${info.message || '未知错误'}`)
    } finally {
      setPrimaryLoading(false)
    }
  }

  const dismiss = async () => {
    if (dismissLoading) return
    setDismissLoading(true)
    try {
      const updated = await onboardingApi.dismissOnboarding({
        expectedVersion: journey.preference.preference_version,
      })
      setJourney(updated)
      setAnnouncement('已暂存首次引导；稍后可在设置中重新打开。')
      if (!updated?.should_enter_welcome) {
        navigate('/today')
      }
    } catch (err) {
      const info = normalizeApiError(err)
      setError(info.message || '暂时无法暂存首次引导')
    } finally {
      setDismissLoading(false)
    }
  }

  if (state === 'loading') {
    return (
      <div className="welcome-page page-stack">
        <header className="page-header">
          <p className="eyebrow">首次使用</p>
          <h1>欢迎</h1>
        </header>
        <div className="inline-state" role="status">
          <Loader2 size={16} className="spinner" />
          <span>正在准备你的首次学习旅程…</span>
        </div>
        <div role="status" aria-live="polite" className="visually-hidden">{announcement}</div>
      </div>
    )
  }

  if (state === 'error' && !journey) {
    return (
      <div className="welcome-page page-stack">
        <header className="page-header">
          <p className="eyebrow">首次使用</p>
          <h1>欢迎</h1>
        </header>
        <div className="inline-error" role="alert">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
        <button type="button" className="button button--secondary" onClick={loadJourney}>
          重新尝试
        </button>
        <div role="status" aria-live="polite" className="visually-hidden">{announcement}</div>
      </div>
    )
  }

  const isRecovery = nextAction.kind === 'recover'
  const primaryLabel = primaryLoading ? '正在处理…' : nextAction.label

  return (
    <div className="welcome-page page-stack">
      <header className="page-header">
        <p className="eyebrow">首次使用</p>
        <h1>欢迎</h1>
        <p>只需要 4 步即可开始第一节：模型 → 资料 → 目标 → 第一节。</p>
      </header>

      <section className="surface welcome-boundary" aria-labelledby="boundary-heading">
        <div>
          <h2 id="boundary-heading">数据与模型说明</h2>
          <p>学习记录与模型调用只保存在本机；不会上传到任何服务端账户。</p>
          {boundaryAcknowledged ? (
            <p className="boundary-status">已确认</p>
          ) : (
            <p className="boundary-status">需要你确认</p>
          )}
        </div>
      </section>

      <section className="surface welcome-steps" aria-label="首次学习四步进度">
        <ol className="step-list">
          {steps.map((step) => (
            <li key={step.step} className={`step ${STATE_CLASS[step.state] || ''}`}>
              <span className="step-title">{step.title || STEP_LABELS[step.step]}</span>
              <span className="step-state" aria-label={`状态 ${STATE_LABEL[step.state] || step.state}`}>
                {STATE_LABEL[step.state] || step.state}
              </span>
              <p className="step-summary">{step.summary}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="surface welcome-actions" aria-label="当前步骤操作">
        {error && (
          <p className="inline-error" role="alert">{error}</p>
        )}
        <div className="welcome-primary-wrap">
          <button
            type="button"
            className={`button button--primary ${isRecovery ? 'button--recovery' : ''}`}
            onClick={primaryAction}
            disabled={!nextAction.enabled || primaryLoading}
            aria-describedby="primary-help"
            aria-label={nextAction.label}
          >
            <span>{primaryLabel}</span>
            {nextAction.enabled && <ChevronRight size={16} aria-hidden />}
          </button>
          <small id="primary-help" className="welcome-primary-help">
            继续下一步；不会自动创建样例数据。
          </small>
        </div>

        <div className="welcome-secondary-actions">
          <button
            type="button"
            className="button button--ghost"
            onClick={dismiss}
            disabled={dismissLoading}
          >
            {dismissLoading ? '正在暂存…' : '稍后再做'}
          </button>
        </div>
      </section>

      <div role="status" aria-live="polite" className="visually-hidden">{announcement}</div>
    </div>
  )
}
