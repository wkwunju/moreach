"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Dropdown from "@/components/Dropdown";
import { getUser, getToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// Industry options relevant to moreach
const INDUSTRIES = [
  { value: "E-commerce", label: "E-commerce" },
  { value: "SaaS", label: "SaaS" },
  { value: "Marketing Agency", label: "Marketing Agency" },
  { value: "Content Creator", label: "Content Creator" },
  { value: "Retail", label: "Retail" },
  { value: "Fashion & Beauty", label: "Fashion & Beauty" },
  { value: "Health & Fitness", label: "Health & Fitness" },
  { value: "Food & Beverage", label: "Food & Beverage" },
  { value: "Technology", label: "Technology" },
  { value: "Education", label: "Education" },
  { value: "Other", label: "Other" },
];

const USAGE_TYPES = [
  { value: "Personal Use", label: "Personal Use - I'm using this for my own business" },
  { value: "Agency Use", label: "Agency Use - I'm managing campaigns for clients" },
  { value: "Team Use", label: "Team Use - I'm part of a marketing team" },
];

export default function CompleteProfilePage() {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState("");
  const [formData, setFormData] = useState({
    full_name: "",
    company: "",
    job_title: "",
    industry: "E-commerce",
    usage_type: "Personal Use",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const user = getUser();
    const token = getToken();

    if (!user || !token) {
      router.push("/login");
      return;
    }

    // If profile is already completed, redirect to dashboard
    if (user.profile_completed) {
      router.push("/reddit");
      return;
    }

    setUserEmail(user.email);
    // Pre-fill name from Google if available
    if (user.full_name) {
      setFormData((prev) => ({ ...prev, full_name: user.full_name }));
    }
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!formData.full_name.trim()) {
      setError("Full name is required");
      return;
    }

    setLoading(true);

    try {
      const token = getToken();
      const response = await fetch(`${API_BASE}/api/v1/auth/complete-profile`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: formData.full_name,
          company: formData.company,
          job_title: formData.job_title,
          industry: formData.industry,
          usage_type: formData.usage_type,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to update profile");
      }

      // Update user in localStorage
      localStorage.setItem("user", JSON.stringify(data));

      // Dispatch auth change event
      window.dispatchEvent(new Event("authChange"));

      // Redirect to dashboard
      router.push("/reddit");
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-2xl">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="text-3xl font-bold text-gray-900">
            moreach.ai
          </Link>
          <p className="text-gray-600 mt-2">Complete your profile</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          {/* Welcome Message */}
          <div className="mb-6 p-4 bg-green-50 rounded-xl">
            <p className="text-green-800">
              Welcome to moreach! Tell us a bit about yourself so we can make your experience more relevant and useful.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}

            {/* Full Name */}
            <div>
              <label htmlFor="full_name" className="block text-sm font-semibold text-gray-900 mb-2">
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                required
                value={formData.full_name}
                onChange={handleChange}
                className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                placeholder="John Doe"
              />
            </div>

            {/* Company & Job Title */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="company" className="block text-sm font-semibold text-gray-900 mb-2">
                  Company
                </label>
                <input
                  type="text"
                  id="company"
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  placeholder="Acme Inc."
                />
              </div>

              <div>
                <label htmlFor="job_title" className="block text-sm font-semibold text-gray-900 mb-2">
                  Job Title
                </label>
                <input
                  type="text"
                  id="job_title"
                  name="job_title"
                  value={formData.job_title}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  placeholder="Marketing Manager"
                />
              </div>
            </div>

            {/* Industry */}
            <div>
              <label htmlFor="industry" className="block text-sm font-semibold text-gray-900 mb-2">
                Industry <span className="text-red-500">*</span>
              </label>
              <Dropdown
                options={INDUSTRIES}
                value={formData.industry}
                onChange={(value) => setFormData({ ...formData, industry: value })}
                placeholder="Select your industry"
                required
              />
            </div>

            {/* Usage Type */}
            <div>
              <label htmlFor="usage_type" className="block text-sm font-semibold text-gray-900 mb-2">
                How will you use moreach? <span className="text-red-500">*</span>
              </label>
              <Dropdown
                options={USAGE_TYPES}
                value={formData.usage_type}
                onChange={(value) => setFormData({ ...formData, usage_type: value })}
                placeholder="Select usage type"
                required
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-gray-900 px-6 py-3 text-base font-semibold text-white transition hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Saving..." : "Continue to Dashboard"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
