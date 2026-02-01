/**
 * Tests for API functions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  createRedditCampaign,
  fetchRedditCampaigns,
  fetchRedditLeads,
  updateLeadStatus,
  pauseCampaign,
  resumeCampaign,
  runCampaignNow,
  deleteCampaign,
  createCheckoutSession,
  createPortalSession,
  generateLeadSuggestions,
} from '@/lib/api'

// Mock authFetch
vi.mock('@/lib/auth', () => ({
  authFetch: vi.fn(),
  getToken: vi.fn(() => 'test-token'),
}))

import { authFetch } from '@/lib/auth'

const mockAuthFetch = authFetch as ReturnType<typeof vi.fn>

describe('Reddit Campaign API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createRedditCampaign', () => {
    it('creates campaign successfully', async () => {
      const mockCampaign = {
        id: 1,
        status: 'DISCOVERING',
        business_description: 'Test business',
      }

      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockCampaign),
      })

      const result = await createRedditCampaign('Test business', 6)

      expect(result.id).toBe(1)
      expect(result.status).toBe('DISCOVERING')
      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('/reddit/campaigns'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Test business'),
        })
      )
    })

    it('throws error on failure', async () => {
      mockAuthFetch.mockResolvedValue({
        ok: false,
        status: 500,
      })

      await expect(createRedditCampaign('Test')).rejects.toThrow('Failed to create Reddit campaign')
    })
  })

  describe('fetchRedditCampaigns', () => {
    it('fetches campaigns successfully', async () => {
      const mockCampaigns = [
        { id: 1, status: 'ACTIVE' },
        { id: 2, status: 'PAUSED' },
      ]

      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockCampaigns),
      })

      const result = await fetchRedditCampaigns()

      expect(result).toHaveLength(2)
      expect(result[0].id).toBe(1)
    })
  })

  describe('fetchRedditLeads', () => {
    it('fetches leads without filter', async () => {
      const mockLeads = {
        campaign_id: 1,
        total_leads: 10,
        leads: [{ id: 1, title: 'Test Lead' }],
      }

      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockLeads),
      })

      const result = await fetchRedditLeads(1)

      expect(result.total_leads).toBe(10)
      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('/campaigns/1/leads'),
        expect.anything()
      )
    })

    it('fetches leads with status filter', async () => {
      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ leads: [] }),
      })

      await fetchRedditLeads(1, 'NEW')

      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('status=NEW'),
        expect.anything()
      )
    })
  })

  describe('updateLeadStatus', () => {
    it('updates lead status', async () => {
      mockAuthFetch.mockResolvedValue({ ok: true })

      await updateLeadStatus(1, 'CONTACTED')

      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('/leads/1/status'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ status: 'CONTACTED' }),
        })
      )
    })
  })

  describe('pauseCampaign', () => {
    it('pauses campaign', async () => {
      mockAuthFetch.mockResolvedValue({ ok: true })

      await pauseCampaign(1)

      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('/campaigns/1/pause'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  describe('resumeCampaign', () => {
    it('resumes campaign', async () => {
      mockAuthFetch.mockResolvedValue({ ok: true })

      await resumeCampaign(1)

      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('/campaigns/1/resume'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  describe('runCampaignNow', () => {
    it('runs campaign immediately', async () => {
      const mockSummary = {
        message: 'Campaign polling completed',
        summary: { posts_fetched: 10 },
      }

      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSummary),
      })

      const result = await runCampaignNow(1)

      expect(result.message).toBe('Campaign polling completed')
    })
  })

  describe('deleteCampaign', () => {
    it('deletes campaign', async () => {
      mockAuthFetch.mockResolvedValue({ ok: true })

      await deleteCampaign(1)

      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('/campaigns/1'),
        expect.objectContaining({ method: 'DELETE' })
      )
    })
  })

  describe('generateLeadSuggestions', () => {
    it('generates suggestions for lead', async () => {
      const mockSuggestions = {
        suggested_comment: 'Test comment',
        suggested_dm: 'Test DM',
        cached: false,
      }

      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSuggestions),
      })

      const result = await generateLeadSuggestions(1)

      expect(result.suggested_comment).toBe('Test comment')
      expect(result.cached).toBe(false)
    })
  })
})

describe('Stripe Billing API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createCheckoutSession', () => {
    it('creates checkout session successfully', async () => {
      const mockResponse = {
        checkout_url: 'https://checkout.stripe.com/test',
        session_id: 'cs_test_123',
      }

      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await createCheckoutSession('STARTER_MONTHLY')

      expect(result.checkout_url).toBe('https://checkout.stripe.com/test')
      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining('/billing/create-checkout-session'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('STARTER_MONTHLY'),
        })
      )
    })

    it('passes custom success/cancel URLs', async () => {
      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ checkout_url: 'url' }),
      })

      await createCheckoutSession(
        'GROWTH_ANNUALLY',
        'https://example.com/success',
        'https://example.com/cancel'
      )

      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          body: expect.stringContaining('success'),
        })
      )
    })

    it('throws error with detail from response', async () => {
      mockAuthFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid tier code' }),
      })

      await expect(createCheckoutSession('INVALID')).rejects.toThrow('Invalid tier code')
    })
  })

  describe('createPortalSession', () => {
    it('creates portal session successfully', async () => {
      const mockResponse = {
        portal_url: 'https://billing.stripe.com/test',
      }

      mockAuthFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await createPortalSession()

      expect(result.portal_url).toBe('https://billing.stripe.com/test')
    })

    it('throws error when no subscription', async () => {
      mockAuthFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'No active subscription found' }),
      })

      await expect(createPortalSession()).rejects.toThrow('No active subscription found')
    })
  })
})
