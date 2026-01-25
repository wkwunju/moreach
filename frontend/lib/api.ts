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

export async function deleteCampaign(campaignId: number): Promise<void> {
  const response = await authFetch(`${baseUrl}/api/v1/reddit/campaigns/${campaignId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error("Failed to delete campaign");
  }
}
