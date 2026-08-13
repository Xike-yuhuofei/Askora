import '@testing-library/jest-dom/vitest'
import '../styles/global.css'
import '../styles/ds.css'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach } from 'vitest'

// jsdom sometimes does not expose a usable localStorage in certain environments.
// Provide a minimal in-memory localStorage so tests that assert no auth/onboarding
// tokens are persisted can run reliably.
const createStorage = () => {
  let store = {}
  return {
    getItem: (key) => (Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value) },
    removeItem: (key) => { delete store[key] },
    clear: () => { store = {} },
    key: (index) => Object.keys(store)[index] ?? null,
    get length() { return Object.keys(store).length },
  }
}

beforeEach(() => {
  const storage = createStorage()
  Object.defineProperty(globalThis, 'localStorage', { value: storage, configurable: true })
})

afterEach(() => {
  cleanup()
})