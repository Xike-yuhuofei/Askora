import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as workspaceApi from '../api/workspace'
import Evidence from '../pages/Evidence'

vi.mock('../api/workspace', () => ({ getEvidenceWorkspace: vi.fn() }))

describe('UI02B-VSLICE-AC-005/008 Evidence', () => {
  beforeEach(() => workspaceApi.getEvidenceWorkspace.mockReset())

  it('shows estimates and named evidence without deriving a mastery label', async () => {
    workspaceApi.getEvidenceWorkspace.mockResolvedValue({ schema_version: '1.0', data: { view_state: 'READY', knowledge_units_assessed: 1, legacy_compatibility: { visible_by_default: false, fields: {}, source_label: 'LEGACY_COMPATIBILITY' }, entries: [{ knowledge_unit_ref: 'knowledge_unit:k1:v3', label: '函数变化', competence_probability: 0.62, confidence: 0.78, independent_success_count: 2, delayed_recall_evidence_count: 1, transfer_evidence_count: 0, evidence_count: 4, effective_evidence_weight: 2.5, active_misconception_ids: [], algorithm_id: 'weighted-bkt', algorithm_version: '1.0', product_label: null, product_label_rule_version: null }] }, source_status: [{ source_system: 'SYS03', availability: 'AVAILABLE', reason_codes: [] }] })
    render(<Evidence />)
    expect(await screen.findByRole('heading', { name: '函数变化' })).toBeInTheDocument()
    expect(screen.getByText('62%（估计）')).toBeInTheDocument()
    expect(screen.getByText('未发布')).toBeInTheDocument()
    expect(screen.queryByText('已掌握')).not.toBeInTheDocument()
  })

  it('does not turn missing evidence into zero', async () => {
    workspaceApi.getEvidenceWorkspace.mockResolvedValue({ schema_version: '1.0', data: { view_state: 'PARTIAL', knowledge_units_assessed: 1, legacy_compatibility: { visible_by_default: false, fields: {}, source_label: 'LEGACY_COMPATIBILITY' }, entries: [{ knowledge_unit_ref: 'knowledge_unit:k1:version-unavailable', label: null, competence_probability: null, confidence: null, independent_success_count: null, delayed_recall_evidence_count: null, transfer_evidence_count: null, evidence_count: null, effective_evidence_weight: null, active_misconception_ids: null, algorithm_id: null, algorithm_version: null, product_label: null, product_label_rule_version: null }] }, source_status: [] })
    render(<Evidence />)
    expect(await screen.findByText('证据不足')).toBeInTheDocument()
    expect(screen.getAllByText('暂无可靠记录').length).toBeGreaterThan(0)
    expect(screen.queryByText('0%（估计）')).not.toBeInTheDocument()
  })
})
