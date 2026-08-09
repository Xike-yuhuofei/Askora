import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const indexPath = resolve(process.cwd(), 'index.html')

function directives() {
  const html = readFileSync(indexPath, 'utf8')
  const policy = html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)?.[1]
  expect(policy).toBeTruthy()
  return Object.fromEntries(policy.split(';').map((directive) => {
    const [name, ...values] = directive.trim().split(/\s+/)
    return [name, values]
  }))
}

describe('frontend Content Security Policy', () => {
  it('只为本机 OCR 原页预览允许 blob 图像', () => {
    const policy = directives()

    expect(policy['img-src']).toContain('blob:')
    expect(policy['script-src']).not.toContain('blob:')
    expect(policy['connect-src']).not.toContain('blob:')
    expect(policy['object-src']).toEqual(["'none'"])
  })
})
