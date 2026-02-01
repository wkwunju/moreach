"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      // Check for error in URL
      const urlError = searchParams.get("error");
      if (urlError) {
        setError(getErrorMessage(urlError));
        return;
      }

      // Get token from URL
      const token = searchParams.get("token");
      const userId = searchParams.get("user");

      if (!token) {
        setError("No authentication token received. Please try again.");
        return;
      }

      // Store token
      localStorage.setItem("token", token);

      // Fetch user data
      try {
        const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch user data");
        }

        const user = await response.json();
        localStorage.setItem("user", JSON.stringify(user));

        // Dispatch auth change event
        window.dispatchEvent(new Event("authChange"));

        // Check if profile is complete
        if (!user.profile_completed) {
          router.replace("/complete-profile");
        } else {
          router.replace("/reddit");
        }
      } catch (err) {
        console.error("Error fetching user:", err);
        setError("Failed to complete authentication. Please try again.");
        localStorage.removeItem("token");
      }
    };

    handleCallback();
  }, [searchParams, router]);

  const getErrorMessage = (errorCode: string): string => {
    switch (errorCode) {
      case "google_auth_failed":
        return "Google authentication failed. Please try again.";
      case "invalid_token":
        return "Invalid authentication token. Please try again.";
      case "no_email":
        return "Could not retrieve email from Google. Please try again.";
      case "account_inactive":
        return "Your account is inactive. Please contact support.";
      default:
        return "Authentication failed. Please try again.";
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-6">
        <div className="w-full max-w-md text-center">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            {/* Error Icon */}
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mb-4">Authentication Failed</h2>
            <p className="text-gray-600 mb-8">{error}</p>

            <div className="space-y-3">
              <Link
                href="/register"
                className="block w-full rounded-xl bg-gray-900 px-6 py-3 text-base font-semibold text-white transition hover:bg-gray-800"
              >
                Try Again
              </Link>
              <Link
                href="/login"
                className="block w-full rounded-xl bg-gray-100 px-6 py-3 text-base font-semibold text-gray-700 transition hover:bg-gray-200"
              >
                Sign in with Email
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-6">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-gray-900 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Completing sign in...</h2>
        <p className="text-gray-600">Please wait while we set up your account.</p>
      </div>
    </div>
  );
}
