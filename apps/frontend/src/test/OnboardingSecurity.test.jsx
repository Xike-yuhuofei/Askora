import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import NewChat from '../pages/NewChat'

/*
  P106 onboarding security boundaries — NewChat 已改为静态复刻页（不再请求
  onboarding / workspace API，也不渲染服务端数据）。保留 DOM 卫生守卫：
  页面任何状态下都不得泄露令牌、原始路径或写入 onboarding 标记。
*/
describe('P106 onboarding security boundaries', () => {
  it('does not render access tokens, refresh tokens or API keys anywhere in the DOM', () => {
    render(<NewChat />)
    const body = document.body.textContent || ''
    expect(body).not.toMatch(/Bearer\s+[A-Za-z0-9._-]+/)
    expect(body).not.toMatch(/access_token/)
    expect(body).not.toMatch(/refresh_token/)
    expect(body).not.toMatch(/sk-[A-Za-z0-9]+/)
  })

  it('does not expose raw source paths (e.g., /Users/, managed/ paths) or stack traces', () => {
    render(<NewChat />)
    const body = document.body.textContent || ''
    expect(body).not.toMatch(/\/Users\//)
    expect(body).not.toMatch(/managed\//)
    expect(body).not.toMatch(/Traceback/)
    expect(body).not.toMatch(/\bFile ".*\.py"/)
  })

  it('does not write completion flags into localStorage', () => {
    render(<NewChat />)
    const keys = []
    for (let i = 0; i < localStorage.length; i += 1) keys.push(localStorage.key(i))
    const onboardingKeys = keys.filter((key) => key?.startsWith('onboarding'))
    expect(onboardingKeys).toEqual([])
  })
})
