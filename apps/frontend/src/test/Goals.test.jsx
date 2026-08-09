import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as workspaceApi from '../api/workspace'
import Goals from '../pages/Goals'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({ getGoalsWorkspace: vi.fn() }))

describe('UI02B-VSLICE-AC-001/008 Goals', () => {
  beforeEach(() => workspaceApi.getGoalsWorkspace.mockReset())

  it('renders latest owner goal facts and version without edit controls', async () => {
    workspaceApi.getGoalsWorkspace.mockResolvedValue({ schema_version: '1.0', data: { view_state: 'READY', goals: [{ goal_ref: 'learning_goal:g1:v2', title: '理解函数变化', topic: '函数', target_capabilities: ['解释函数变化'], success_criteria: ['独立分析新函数'], deadline_at: null, weekly_time_budget_minutes: 90, status: 'active', confirmed_by_user: true }] }, source_status: [{ source_system: 'SYS06', availability: 'AVAILABLE', reason_codes: [] }] })
    render(<RouterProvider><Goals /></RouterProvider>)
    expect(await screen.findByRole('heading', { name: '理解函数变化' })).toBeInTheDocument()
    expect(screen.getByText('v2')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /查看路径/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /编辑|暂停|确认/ })).not.toBeInTheDocument()
  })

  it('keeps an honest empty state', async () => {
    workspaceApi.getGoalsWorkspace.mockResolvedValue({ schema_version: '1.0', data: { view_state: 'EMPTY', goals: [] }, source_status: [] })
    render(<RouterProvider><Goals /></RouterProvider>)
    expect(await screen.findByRole('heading', { name: '还没有学习目标' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '前往资料库' })).toBeInTheDocument()
  })
})
