// Authentication utilities

export type SubscriptionTier = "FREE_TRIAL" | "MONTHLY" | "ANNUALLY" | "EXPIRED";

export interface User {
  id: number;
  email: string;
  full_name: string;
  company: string;
  job_title: string;
  industry: string;
  usage_type: string;
  role: string;
  is_active: boolean;
  email_verified: boolean;
  profile_completed: boolean;
  subscription_tier: SubscriptionTier;
  trial_ends_at: string | null;
  subscription_ends_at: string | null;
  created_at: string;
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem("token");
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem("user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function getTrialDaysRemaining(user: User | null): number {
  if (!user || !user.trial_ends_at) return 0;
  const trialEnd = new Date(user.trial_ends_at);
  const now = new Date();
  const diffTime = trialEnd.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return Math.max(0, diffDays);
}

export function isTrialActive(user: User | null): boolean {
  if (!user) return false;
  if (user.subscription_tier !== "FREE_TRIAL") return false;
  return getTrialDaysRemaining(user) > 0;
}

export function isSubscriptionActive(user: User | null): boolean {
  if (!user) return false;
  if (user.subscription_tier === "MONTHLY" || user.subscription_tier === "ANNUALLY") {
    if (!user.subscription_ends_at) return true; // Active indefinitely
    const subEnd = new Date(user.subscription_ends_at);
    return subEnd > new Date();
  }
  return isTrialActive(user);
}

export function logout() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  // Dispatch auth change event for components to update
  window.dispatchEvent(new Event("authChange"));
}

/**
 * Refresh user data from backend (especially subscription status)
 * This ensures subscription/trial info is always fresh and can't be bypassed via localStorage
 */
export async function refreshUser(): Promise<User | null> {
  if (typeof window === 'undefined') return null;

  const token = getToken();
  if (!token) return null;

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  try {
    const response = await fetch(`${baseUrl}/api/v1/auth/me`, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired/invalid, logout
        logout();
        return null;
      }
      throw new Error("Failed to refresh user");
    }

    const freshUser = await response.json();

    // Update localStorage with fresh data
    localStorage.setItem("user", JSON.stringify(freshUser));

    // Dispatch event so components can update
    window.dispatchEvent(new Event("authChange"));

    return freshUser;
  } catch (error) {
    console.error("Failed to refresh user:", error);
    return getUser(); // Fall back to cached user
  }
}

// API fetch wrapper that automatically includes auth token
export async function authFetch(url: string, options: RequestInit = {}) {
  const token = getToken();
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // If unauthorized, clear auth and redirect to login
  if (response.status === 401) {
    logout();
    if (typeof window !== 'undefined') {
      window.location.href = "/login";
    }
  }

  return response;
}

