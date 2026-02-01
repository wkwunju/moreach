/**
 * Tests for authentication utilities
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getToken,
  getUser,
  isAuthenticated,
  getTrialDaysRemaining,
  isTrialActive,
  isSubscriptionActive,
  logout,
  refreshUser,
  User,
} from '@/lib/auth'

// Mock user data
const mockTrialUser: User = {
  id: 1,
  email: 'test@example.com',
  full_name: 'Test User',
  company: 'Test Company',
  job_title: 'Developer',
  industry: 'TECHNOLOGY',
  usage_type: 'LEAD_GENERATION',
  role: 'USER',
  is_active: true,
  email_verified: true,
  profile_completed: true,
  subscription_tier: 'FREE_TRIAL',
  trial_ends_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
  subscription_ends_at: null,
  created_at: new Date().toISOString(),
}

const mockPaidUser: User = {
  ...mockTrialUser,
  subscription_tier: 'MONTHLY',
  trial_ends_at: null,
  subscription_ends_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
}

const mockExpiredUser: User = {
  ...mockTrialUser,
  subscription_tier: 'EXPIRED',
  trial_ends_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
}

describe('getToken', () => {
  it('returns null when no token exists', () => {
    expect(getToken()).toBeNull()
  })

  it('returns token when it exists', () => {
    vi.spyOn(localStorage, 'getItem').mockReturnValue('test-token-123')
    expect(getToken()).toBe('test-token-123')
  })
})

describe('getUser', () => {
  it('returns null when no user exists', () => {
    expect(getUser()).toBeNull()
  })

  it('returns parsed user when it exists', () => {
    vi.spyOn(localStorage, 'getItem').mockReturnValue(JSON.stringify(mockTrialUser))
    const user = getUser()
    expect(user).not.toBeNull()
    expect(user?.email).toBe('test@example.com')
  })

  it('returns null for invalid JSON', () => {
    vi.spyOn(localStorage, 'getItem').mockReturnValue('invalid json')
    expect(getUser()).toBeNull()
  })
})

describe('isAuthenticated', () => {
  it('returns false when no token', () => {
    expect(isAuthenticated()).toBe(false)
  })

  it('returns true when token exists', () => {
    vi.spyOn(localStorage, 'getItem').mockReturnValue('test-token')
    expect(isAuthenticated()).toBe(true)
  })
})

describe('getTrialDaysRemaining', () => {
  it('returns 0 for null user', () => {
    expect(getTrialDaysRemaining(null)).toBe(0)
  })

  it('returns 0 for user without trial_ends_at', () => {
    const user = { ...mockTrialUser, trial_ends_at: null }
    expect(getTrialDaysRemaining(user)).toBe(0)
  })

  it('returns correct days remaining for active trial', () => {
    const days = getTrialDaysRemaining(mockTrialUser)
    expect(days).toBeGreaterThan(0)
    expect(days).toBeLessThanOrEqual(7)
  })

  it('returns 0 for expired trial', () => {
    expect(getTrialDaysRemaining(mockExpiredUser)).toBe(0)
  })
})

describe('isTrialActive', () => {
  it('returns false for null user', () => {
    expect(isTrialActive(null)).toBe(false)
  })

  it('returns true for user with active trial', () => {
    expect(isTrialActive(mockTrialUser)).toBe(true)
  })

  it('returns false for paid user', () => {
    expect(isTrialActive(mockPaidUser)).toBe(false)
  })

  it('returns false for expired user', () => {
    expect(isTrialActive(mockExpiredUser)).toBe(false)
  })
})

describe('isSubscriptionActive', () => {
  it('returns false for null user', () => {
    expect(isSubscriptionActive(null)).toBe(false)
  })

  it('returns true for user with active trial', () => {
    expect(isSubscriptionActive(mockTrialUser)).toBe(true)
  })

  it('returns true for paid monthly user', () => {
    expect(isSubscriptionActive(mockPaidUser)).toBe(true)
  })

  it('returns true for paid annually user', () => {
    const annualUser = { ...mockPaidUser, subscription_tier: 'ANNUALLY' as const }
    expect(isSubscriptionActive(annualUser)).toBe(true)
  })

  it('returns false for expired user', () => {
    expect(isSubscriptionActive(mockExpiredUser)).toBe(false)
  })

  it('returns true for paid user without end date', () => {
    const userNoEndDate = { ...mockPaidUser, subscription_ends_at: null }
    expect(isSubscriptionActive(userNoEndDate)).toBe(true)
  })

  it('returns false for paid user with past end date', () => {
    const expiredPaidUser = {
      ...mockPaidUser,
      subscription_ends_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // Yesterday
    }
    expect(isSubscriptionActive(expiredPaidUser)).toBe(false)
  })
})

describe('logout', () => {
  it('removes token and user from localStorage', () => {
    logout()
    expect(localStorage.removeItem).toHaveBeenCalledWith('token')
    expect(localStorage.removeItem).toHaveBeenCalledWith('user')
  })

  it('dispatches authChange event', () => {
    logout()
    expect(window.dispatchEvent).toHaveBeenCalled()
  })
})

describe('refreshUser', () => {
  beforeEach(() => {
    vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
      if (key === 'token') return 'test-token'
      if (key === 'user') return JSON.stringify(mockTrialUser)
      return null
    })
  })

  it('returns null when no token', async () => {
    vi.spyOn(localStorage, 'getItem').mockReturnValue(null)
    const user = await refreshUser()
    expect(user).toBeNull()
  })

  it('fetches user from API and updates localStorage', async () => {
    const freshUser = { ...mockTrialUser, full_name: 'Updated Name' }
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(freshUser),
    })

    const user = await refreshUser()

    expect(user?.full_name).toBe('Updated Name')
    expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(freshUser))
    expect(window.dispatchEvent).toHaveBeenCalled()
  })

  it('logs out on 401 response', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 401,
    })

    const user = await refreshUser()

    expect(user).toBeNull()
    expect(localStorage.removeItem).toHaveBeenCalledWith('token')
  })

  it('returns cached user on network error', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network error'))

    const user = await refreshUser()

    expect(user).not.toBeNull()
    expect(user?.email).toBe('test@example.com')
  })
})
