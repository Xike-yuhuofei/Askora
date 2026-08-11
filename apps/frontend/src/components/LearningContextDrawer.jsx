import { useEffect, useId, useRef, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

import { getLearningContext } from '../api/workspace'
import './LearningContextDrawer.css'

function presentation(state) {
  const data = state.data
  const firstDirection = data?.next_directions?.[0]?.label
  const stage = data?.stage_name || '当前阶段信息不可用'
  const goal = data?.stage_goal || '阶段目标信息不可用'
  const next = firstDirection || '方向信息不可用'

  if (state.status === 'LOADING') {
    return {
      summary: '正在读取当前阶段 · 接下来',
      stage: '正在读取当前阶段',
      goal: '正在读取阶段目标',
      next: [],
    }
  }
  if (state.status === 'ERROR') {
    return {
      summary: '当前阶段信息读取失败 · 接下来：暂不可用',
      stage: '当前阶段信息读取失败',
      goal: '阶段目标信息读取失败',
      next: [],
    }
  }
  if (data.view_state === 'MISSING') {
    return {
      summary: '当前阶段信息不可用 · 接下来：方向信息不可用',
      stage,
      goal,
      next: [],
    }
  }

  const prefix = data.view_state === 'PARTIAL'
    ? '部分信息'
    : data.view_state === 'STALE'
      ? '信息可能已过期'
      : ''
  return {
    summary: `${prefix ? `${prefix} · ` : ''}${stage} · 接下来：${next}`,
    stage: `${prefix ? `${prefix}：` : ''}${stage}`,
    goal,
    next: (data.next_directions || []).slice(0, 3),
  }
}

export default function LearningContextDrawer({ activityId }) {
  const [expanded, setExpanded] = useState(false)
  const [state, setState] = useState({ status: 'LOADING', data: null })
  const triggerRef = useRef(null)
  const panelId = useId()

  useEffect(() => {
    let cancelled = false
    setState({ status: 'LOADING', data: null })
    getLearningContext(activityId)
      .then((response) => {
        if (!cancelled) setState({ status: response.data.view_state, data: response.data })
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'ERROR', data: null })
      })
    return () => { cancelled = true }
  }, [activityId])

  const content = presentation(state)
  const collapseAndFocus = () => {
    setExpanded(false)
    window.requestAnimationFrame(() => triggerRef.current?.focus())
  }

  return (
    <section
      className="learning-context-disclosure"
      data-state={state.status}
      aria-label={`学习上下文，状态：${state.status}`}
      onKeyDown={(event) => {
        if (event.key === 'Escape' && expanded) {
          event.preventDefault()
          collapseAndFocus()
        }
      }}
    >
      <button
        ref={triggerRef}
        type="button"
        className="learning-context-disclosure__trigger"
        aria-expanded={expanded}
        aria-controls={panelId}
        aria-label={`${expanded ? '收起' : '展开'}学习上下文：${content.summary}`}
        onClick={() => setExpanded((current) => !current)}
      >
        <span className="learning-context-disclosure__summary">{content.summary}</span>
        {expanded ? <ChevronUp size={17} aria-hidden="true" /> : <ChevronDown size={17} aria-hidden="true" />}
      </button>

      {expanded && (
        <div
          id={panelId}
          className="learning-context-disclosure__panel"
          role="group"
          aria-label="学习上下文详情"
        >
          <dl className="learning-context-disclosure__facts">
            <div>
              <dt>当前阶段</dt>
              <dd>{content.stage}</dd>
            </div>
            <div>
              <dt>阶段目标</dt>
              <dd>{content.goal}</dd>
            </div>
          </dl>
          <div className="learning-context-disclosure__next">
            <h3>接下来</h3>
            {content.next.length > 0 ? (
              <ol>
                {content.next.map((direction) => (
                  <li key={direction.ref}>{direction.label}</li>
                ))}
              </ol>
            ) : (
              <p>方向信息不可用</p>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
