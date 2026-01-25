// Authentication utilities

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

export function logout() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

// API fetch wrapper that automatically includes auth token
export async function authFetch(url: string, options: RequestInit = {}) {
  const token = getToken();
  
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
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

