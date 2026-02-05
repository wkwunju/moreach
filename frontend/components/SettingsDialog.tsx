"use client";

import { useState, useEffect } from "react";
import { User } from "@/lib/auth";
import { updateProfile, ProfileUpdateData } from "@/lib/api";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  onUpdate?: (user: User) => void;
}

const INDUSTRY_OPTIONS = [
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

const USAGE_TYPE_OPTIONS = [
  { value: "Personal Use", label: "Personal Use" },
  { value: "Agency Use", label: "Agency Use" },
  { value: "Team Use", label: "Team Use" },
];

export default function SettingsDialog({ isOpen, onClose, user, onUpdate }: SettingsDialogProps) {
  const [formData, setFormData] = useState<ProfileUpdateData>({
    full_name: "",
    company: "",
    job_title: "",
    industry: "Other",
    usage_type: "Personal Use",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Initialize form with user data when dialog opens
  useEffect(() => {
    if (isOpen && user) {
      setFormData({
        full_name: user.full_name || "",
        company: user.company || "",
        job_title: user.job_title || "",
        industry: user.industry || "Other",
        usage_type: user.usage_type || "Personal Use",
      });
      setError(null);
      setSuccess(false);
    }
  }, [isOpen, user]);

  if (!isOpen || !user) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await updateProfile(formData);
      setSuccess(true);

      // Update parent component if callback provided
      if (onUpdate) {
        const updatedUser = { ...user, ...formData };
        onUpdate(updatedUser);
      }

      // Close dialog after a short delay to show success message
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof ProfileUpdateData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900">Account Settings</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Email (read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={user.email}
              disabled
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-500 cursor-not-allowed"
            />
            <p className="mt-1 text-xs text-gray-400">Email cannot be changed</p>
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => handleChange("full_name", e.target.value)}
              required
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
              placeholder="Your full name"
            />
          </div>

          {/* Company */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Company
            </label>
            <input
              type="text"
              value={formData.company}
              onChange={(e) => handleChange("company", e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
              placeholder="Your company name"
            />
          </div>

          {/* Job Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Job Title
            </label>
            <input
              type="text"
              value={formData.job_title}
              onChange={(e) => handleChange("job_title", e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
              placeholder="Your job title"
            />
          </div>

          {/* Industry */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Industry
            </label>
            <select
              value={formData.industry}
              onChange={(e) => handleChange("industry", e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all bg-white"
            >
              {INDUSTRY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Usage Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Usage Type
            </label>
            <select
              value={formData.usage_type}
              onChange={(e) => handleChange("usage_type", e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all bg-white"
            >
              {USAGE_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-xl text-green-600 text-sm flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              Profile updated successfully!
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.full_name.trim()}
              className="flex-1 px-4 py-2.5 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
