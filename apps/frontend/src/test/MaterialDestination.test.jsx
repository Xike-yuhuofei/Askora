import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as documentApi from '../api/documents'
import * as onboardingApi from '../api/onboarding'
import * as workspaceApi from '../api/workspace'
import MaterialDestination from '../components/MaterialDestination'

vi.mock('../api/documents', () => ({
  assignMaterial: vi.fn(),
}))

vi.mock('../api/onboarding', () => ({
  getOnboardingJourney: vi.fn(),
}))

vi.mock('../api/workspace', () => ({
  listWorkspaces: vi.fn(),
  createWorkspace: vi.fn(),
  clearTransitionGuard: vi.fn(() => ({
    composer_draft: 'CLEAR',
    stream: 'CLEAR',
    user_note: 'CLEAR',
    material_position: 'PRESERVED',
  })),
}))

const material = {
  document_id: 'doc-1',
  title: '极限.md',
  processing_status: 'completed',
  lifecycle_version: 1,
}

describe('material destination after upload', () => {
  beforeEach(() => {
    documentApi.assignMaterial.mockReset()
    workspaceApi.listWorkspaces.mockReset()
    workspaceApi.createWorkspace.mockReset()
    onboardingApi.getOnboardingJourney.mockReset()
    onboardingApi.getOnboardingJourney.mockResolvedValue({
      steps: [{ step: 'MODEL', state: 'COMPLETE' }],
    })
    workspaceApi.listWorkspaces.mockResolvedValue({
      data: {
        selection_version: 1,
        workspaces: [{ workspace_id: 'ws-1', display_name: '微积分' }],
      },
    })
  })

  it('assigns a processed material to the selected space', async () => {
    const onAssigned = vi.fn()
    documentApi.assignMaterial.mockResolvedValue({
      outcome: 'ASSIGNED',
      workspace_id: 'ws-1',
    })
    render(<MaterialDestination material={material} onAssigned={onAssigned} onDismiss={() => {}} />)
    fireEvent.change(await screen.findByRole('combobox', { name: '已有空间' }), { target: { value: 'ws-1' } })
    fireEvent.click(await screen.findByRole('button', { name: '加入所选空间' }))
    await waitFor(() => expect(documentApi.assignMaterial).toHaveBeenCalledWith('doc-1', expect.objectContaining({
      workspace_id: 'ws-1',
      expected_lifecycle_version: 1,
    })))
    expect(onAssigned).toHaveBeenCalledWith('ws-1', undefined)
  })

  it('starts grounded learning by assigning then telling the parent to open book-learning', async () => {
    const onAssigned = vi.fn()
    workspaceApi.createWorkspace.mockResolvedValue({
      workspace: { workspace_id: 'ws-new' },
    })
    documentApi.assignMaterial.mockResolvedValue({
      outcome: 'ASSIGNED',
      workspace_id: 'ws-new',
    })
    render(<MaterialDestination material={material} onAssigned={onAssigned} onDismiss={() => {}} />)
    fireEvent.click(await screen.findByRole('button', { name: '马上开始学习' }))
    await waitFor(() => expect(onAssigned).toHaveBeenCalledWith('ws-new', {
      startNow: true,
      documentId: 'doc-1',
    }))
  })

  it('does not offer start-now until processing is complete', async () => {
    render(
      <MaterialDestination
        material={{ ...material, processing_status: 'processing' }}
        onAssigned={vi.fn()}
        onDismiss={() => {}}
      />,
    )
    expect(await screen.findByRole('button', { name: '马上开始学习' })).toBeDisabled()
    expect(documentApi.assignMaterial).not.toHaveBeenCalled()
  })
})
