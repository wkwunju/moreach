import type { RequestResponse, ResultsResponse, RedditCampaign, SubredditInfo, RedditLeadsResponse } from "./types";
import { authFetch } from "./auth";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// ======= Instagram API =======

export async function createRequest(description: string, constraints: string): Promise<RequestResponse> {
  const response = await fetch(`${baseUrl}/api/v1/requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description, constraints })
  });

  if (!response.ok) {
    throw new Error("Failed to create request");
  }

  return response.json();
}

export async function fetchResults(requestId: number): Promise<ResultsResponse> {
  const response = await fetch(`${baseUrl}/api/v1/requests/${requestId}/results`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to load results");
  }

  return response.json();
}

// ======= Reddit API =======

export async function createRedditCampaign(businessDescription: string, pollIntervalHours: number = 6): Promise<RedditCampaign> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns`, {
    method: "POST",
    body: JSON.stringify({ 
      business_description: businessDescription,
      poll_interval_hours: pollIntervalHours 
    })
  });

  if (!response.ok) {
    throw new Error("Failed to create Reddit campaign");
  }

  return response.json();
}

export async function discoverSubreddits(campaignId: number): Promise<SubredditInfo[]> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/discover-subreddits`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to discover subreddits");
  }

  return response.json();
}

export async function selectSubreddits(campaignId: number, subreddits: SubredditInfo[]): Promise<void> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/select-subreddits`, {
    method: "POST",
    body: JSON.stringify({ subreddits })
  });

  if (!response.ok) {
    throw new Error("Failed to select subreddits");
  }
}

export async function fetchCampaignSubreddits(campaignId: number): Promise<SubredditInfo[]> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/subreddits`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to fetch campaign subreddits");
  }

  return response.json();
}

export async function fetchRedditCampaigns(): Promise<RedditCampaign[]> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to fetch campaigns");
  }

  return response.json();
}

export async function fetchRedditCampaign(campaignId: number): Promise<RedditCampaign> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to fetch campaign");
  }

  return response.json();
}

export async function fetchRedditLeads(campaignId: number, status?: string): Promise<RedditLeadsResponse> {
  const url = status 
    ? `${baseUrl}/api/v1/reddit/campaigns/${campaignId}/leads?status=${status}`
    : `${baseUrl}/api/v1/reddit/campaigns/${campaignId}/leads`;
    
  const response = await authFetch(url, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Failed to fetch leads");
  }

  return response.json();
}

export async function updateLeadStatus(leadId: number, status: string): Promise<void> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/leads/${leadId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });

  if (!response.ok) {
    throw new Error("Failed to update lead status");
  }
}

export async function pauseCampaign(campaignId: number): Promise<void> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/pause`, {
    method: "POST"
  });

  if (!response.ok) {
    throw new Error("Failed to pause campaign");
  }
}

export async function resumeCampaign(campaignId: number): Promise<void> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/resume`, {
    method: "POST"
  });

  if (!response.ok) {
    throw new Error("Failed to resume campaign");
  }
}

export async function runCampaignNow(campaignId: number): Promise<{ message: string; summary: any }> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/run-now`, {
    method: "POST"
  });

  if (!response.ok) {
    throw new Error("Failed to run campaign");
  }

  return response.json();
}

// ======= SSE Streaming API =======

export interface SSEProgressEvent {
  phase: "fetching" | "scoring" | "suggestions";
  current: number;
  total: number;
  subreddit?: string;
  posts_found?: number;
  message?: string;
  error?: string;
}

export interface SSELeadEvent {
  id: number;
  title: string;
  relevancy_score: number;
  subreddit_name: string;
  has_suggestions: boolean;
  author?: string;
}

export interface SSECompleteEvent {
  total_leads: number;
  total_posts_fetched: number;
  subreddits_polled?: number;
  relevancy_distribution?: Record<string, number>;
  subreddit_distribution?: Record<string, number>;
  message?: string;
}

export interface SSEErrorEvent {
  message: string;
}

export type SSEEvent =
  | { type: "progress"; data: SSEProgressEvent }
  | { type: "lead"; data: SSELeadEvent }
  | { type: "complete"; data: SSECompleteEvent }
  | { type: "error"; data: SSEErrorEvent };

/**
 * Run campaign with SSE streaming updates
 * Returns a cleanup function to abort the stream
 */
export function runCampaignNowStream(
  campaignId: number,
  onEvent: (event: SSEEvent) => void,
  onError: (error: Error) => void
): () => void {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const url = `${baseUrl}/api/v1/reddit/campaigns/${campaignId}/run-now/stream`;

  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "text/event-stream",
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";

        for (const chunk of chunks) {
          if (!chunk.trim()) continue;

          const eventMatch = chunk.match(/event: (\w+)/);
          const dataMatch = chunk.match(/data: (.+)/s);

          if (eventMatch && dataMatch) {
            try {
              const event: SSEEvent = {
                type: eventMatch[1] as SSEEvent["type"],
                data: JSON.parse(dataMatch[1]),
              };
              onEvent(event);
            } catch (e) {
              console.error("Failed to parse SSE event:", e, chunk);
            }
          }
        }
      }
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
        onError(error as Error);
      }
    }
  })();

  // Return cleanup function
  return () => controller.abort();
}

/**
 * Generate suggestions on-demand for a lead
 */
export async function generateLeadSuggestions(leadId: number): Promise<{
  suggested_comment: string;
  suggested_dm: string;
  cached: boolean;
}> {
  const response = await authFetch(
    `${baseUrl}/api/v1/reddit/leads/${leadId}/generate-suggestions`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to generate suggestions");
  }

  return response.json();
}

export async function deleteCampaign(campaignId: number): Promise<void> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error("Failed to delete campaign");
  }
}

// ======= Stripe Billing API =======

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
}

export interface PortalSessionResponse {
  portal_url: string;
}

export async function createCheckoutSession(
  tierCode: string,
  successUrl?: string,
  cancelUrl?: string
): Promise<CheckoutSessionResponse> {
  const response = await authFetch(`${baseUrl}/api/v1/billing/create-checkout-session`, {
    method: "POST",
    body: JSON.stringify({
      tier_code: tierCode,
      success_url: successUrl,
      cancel_url: cancelUrl,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create checkout session" }));
    throw new Error(error.detail || "Failed to create checkout session");
  }

  return response.json();
}

export async function createPortalSession(): Promise<PortalSessionResponse> {
  const response = await authFetch(`${baseUrl}/api/v1/billing/create-portal-session`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create portal session" }));
    throw new Error(error.detail || "Failed to create portal session");
  }

  return response.json();
}
