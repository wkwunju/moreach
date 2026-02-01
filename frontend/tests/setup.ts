/**
 * Vitest test setup file
 */

import { afterEach, beforeEach, vi } from 'vitest'
import '@testing-library/jest-dom'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock window.dispatchEvent
window.dispatchEvent = vi.fn()

// Mock fetch
global.fetch = vi.fn()

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
  localStorageMock.getItem.mockReturnValue(null)
})

afterEach(() => {
  vi.clearAllMocks()
})

// Mock environment variables
vi.stubEnv('NEXT_PUBLIC_API_BASE', 'http://localhost:8000')
