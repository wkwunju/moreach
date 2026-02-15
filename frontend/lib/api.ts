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
    }),
    timeoutMs: 120000,
  });

  if (!response.ok) {
    throw new Error("Failed to create Reddit campaign");
  }

  return response.json();
}

export async function discoverSubreddits(campaignId: number): Promise<SubredditInfo[]> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/discover-subreddits`, {
    cache: "no-store",
    timeoutMs: 120000,
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
  reddit_post_id: string;
  title: string;
  content: string;
  author: string;
  post_url: string;
  score: number;
  num_comments: number;
  created_utc: number;
  relevancy_score: number;
  relevancy_reason: string;
  suggested_comment: string;
  suggested_dm: string;
  subreddit_name: string;
  has_suggestions: boolean;
  status: string;
  discovered_at: string;
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

// ======= Background Polling API =======

export interface PollTaskStatus {
  task_id: string | null;
  status: "running" | "completed" | "failed" | null;
  phase: string;
  current: number;
  total: number;
  message: string;
  leads_created: number;
  leads: number[];
  error: string | null;
  started_at?: string;
  completed_at?: string;
  summary?: SSECompleteEvent;
}

/**
 * Start a background poll task for a campaign
 * Returns immediately with task_id - use getPollStatus to check progress
 *
 * @param campaignId - The campaign to poll
 * @param force - If true, clears any stuck task status and starts fresh
 */
export async function startPollAsync(campaignId: number, force: boolean = false): Promise<{
  message: string;
  task_id: string;
  already_running: boolean;
}> {
  const url = force
    ? `${baseUrl}/api/v1/reddit/campaigns/${campaignId}/poll-async?force=true`
    : `${baseUrl}/api/v1/reddit/campaigns/${campaignId}/poll-async`;

  const response = await authFetch(url, {
    method: "POST"
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to start poll" }));
    throw new Error(error.detail || "Failed to start poll");
  }

  return response.json();
}

/**
 * Get the status of a running or completed poll task
 */
export async function getPollStatus(campaignId: number): Promise<PollTaskStatus> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}/poll-status`);

  if (!response.ok) {
    throw new Error("Failed to get poll status");
  }

  return response.json();
}

/**
 * Run campaign poll with automatic polling for updates
 * Starts a background task and polls for status updates
 *
 * @param campaignId - The campaign to poll
 * @param onProgress - Callback for progress updates
 * @param onComplete - Callback when polling completes
 * @param onError - Callback for errors
 * @param pollInterval - How often to check status (ms), default 3000
 * @param force - If true, clears any stuck task status and starts fresh
 * @returns Cleanup function to stop polling
 */
export function runCampaignPoll(
  campaignId: number,
  onProgress: (status: PollTaskStatus) => void,
  onComplete: (status: PollTaskStatus) => void,
  onError: (error: Error) => void,
  pollInterval: number = 3000,
  force: boolean = false
): () => void {
  let stopped = false;
  let intervalId: NodeJS.Timeout | null = null;

  const checkStatus = async () => {
    if (stopped) return;

    try {
      const status = await getPollStatus(campaignId);

      if (stopped) return;

      if (status.status === "running") {
        onProgress(status);
      } else if (status.status === "completed") {
        onComplete(status);
        stop();
      } else if (status.status === "failed") {
        onError(new Error(status.error || "Poll failed"));
        stop();
      }
    } catch (error) {
      if (!stopped) {
        onError(error as Error);
        stop();
      }
    }
  };

  const stop = () => {
    stopped = true;
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };

  // Start the background task
  startPollAsync(campaignId, force)
    .then((result) => {
      if (stopped) return;

      // Start polling for status updates
      checkStatus(); // Check immediately
      intervalId = setInterval(checkStatus, pollInterval);
    })
    .catch((error) => {
      if (!stopped) {
        onError(error);
      }
    });

  return stop;
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

export async function analyzeUrl(url: string): Promise<{ description: string; url: string }> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/analyze-url`, {
    method: "POST",
    body: JSON.stringify({ url }),
    timeoutMs: 60000,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to analyze URL" }));
    throw new Error(error.detail || "Failed to analyze URL");
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

// ======= Profile API =======

export interface ProfileUpdateData {
  full_name: string;
  company: string;
  job_title: string;
  industry: string;
  usage_type: string;
}

export async function updateProfile(data: ProfileUpdateData): Promise<void> {
  const response = await authFetch(`${baseUrl}/api/v1/auth/complete-profile`, {
    method: "POST",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to update profile" }));
    throw new Error(error.detail || "Failed to update profile");
  }

  // Update local storage with new user data
  const updatedUser = await response.json();
  if (typeof window !== "undefined") {
    localStorage.setItem("user", JSON.stringify(updatedUser));
    window.dispatchEvent(new Event("authChange"));
  }
}

// ======= Plan Limits API =======

export interface PlanUsageResponse {
  profile_count: number;
  max_profiles: number;
  profiles_remaining: number;
  can_create_profile: boolean;
  current_plan: string;
  tier_group: string;
  next_tier: string | null;
}

export interface PlanLimitsResponse {
  plan_name: string;
  tier_group: string;
  max_profiles: number;
  max_subreddits_per_profile: number;
  max_leads_per_month: number;
  polls_per_day: number;
  next_tier: string | null;
}

export interface LimitCheckResponse {
  allowed: boolean;
  reason: string | null;
  current_count: number;
  max_count: number;
  upgrade_to: string | null;
  current_plan: string;
}

export interface SubredditLimitCheckResponse {
  allowed: boolean;
  reason: string | null;
  selected_count: number;
  max_count: number;
  upgrade_to: string | null;
  current_plan: string;
}

/**
 * Get current user's plan usage status
 */
export async function getPlanUsage(): Promise<PlanUsageResponse> {
  const response = await authFetch(`${baseUrl}/api/v1/plan/usage`);

  if (!response.ok) {
    throw new Error("Failed to get plan usage");
  }

  return response.json();
}

/**
 * Get the limits for the user's current plan
 */
export async function getPlanLimits(): Promise<PlanLimitsResponse> {
  const response = await authFetch(`${baseUrl}/api/v1/plan/limits`);

  if (!response.ok) {
    throw new Error("Failed to get plan limits");
  }

  return response.json();
}

/**
 * Check if user can create a new business profile
 */
export async function checkCanCreateProfile(): Promise<LimitCheckResponse> {
  const response = await authFetch(`${baseUrl}/api/v1/plan/check-create-profile`);

  if (!response.ok) {
    throw new Error("Failed to check profile limit");
  }

  return response.json();
}

/**
 * Check if user can select the specified number of subreddits
 */
export async function checkSubredditLimit(
  campaignId: number,
  count: number
): Promise<SubredditLimitCheckResponse> {
  const response = await authFetch(
    `${baseUrl}/api/v1/plan/check-subreddit-limit/${campaignId}?count=${count}`
  );

  if (!response.ok) {
    throw new Error("Failed to check subreddit limit");
  }

  return response.json();
}
