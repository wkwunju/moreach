"use client";

import { useState } from "react";
import { User, getTrialDaysRemaining, isTrialActive } from "@/lib/auth";
import { createCheckoutSession, createPortalSession } from "@/lib/api";

type UpgradeReason = "profile_limit" | "subreddit_limit";

interface UpgradeContext {
  reason: UpgradeReason;
  currentCount: number;
  maxCount: number;
  recommendedTier: string; // "GROWTH" or "PRO"
}

interface BillingDialogProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  upgradeContext?: UpgradeContext; // Optional upgrade prompt context
}

const UPGRADE_MESSAGES = {
  profile_limit: {
    title: "Profile limit reached",
    description: (current: number, max: number) =>
      `You've used ${max} of ${max} profiles on your plan.`,
  },
  subreddit_limit: {
    title: "Subreddit limit reached",
    description: (current: number, max: number) =>
      `You can monitor up to ${max} subreddits on your plan.`,
  },
};

export default function BillingDialog({ isOpen, onClose, user, upgradeContext }: BillingDialogProps) {
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "annually">("annually");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !user) return null;

  const trialDaysRemaining = getTrialDaysRemaining(user);
  const trialActive = isTrialActive(user);
  const currentTier = user.subscription_tier;
  // Support both old format (MONTHLY, ANNUALLY) and new format (STARTER_MONTHLY, etc.)
  const isPaid = currentTier === "MONTHLY" ||
    currentTier === "ANNUALLY" ||
    currentTier?.startsWith("STARTER") ||
    currentTier?.startsWith("GROWTH") ||
    currentTier?.startsWith("PRO");

  // Tier hierarchy for upgrade logic
  const tierHierarchy: Record<string, number> = {
    "FREE_TRIAL": 0,
    "EXPIRED": 0,
    "STARTER_MONTHLY": 1,
    "STARTER_ANNUALLY": 2,
    "GROWTH_MONTHLY": 3,
    "GROWTH_ANNUALLY": 4,
    "PRO_MONTHLY": 5,
    "PRO_ANNUALLY": 6,
  };

  const getCurrentTierLevel = () => tierHierarchy[currentTier || "FREE_TRIAL"] || 0;

  const getPlanTierCode = (planId: string) => {
    return billingPeriod === "monthly"
      ? `${planId.toUpperCase()}_MONTHLY`
      : `${planId.toUpperCase()}_ANNUALLY`;
  };

  const isCurrentPlan = (planId: string) => {
    const planTierCode = getPlanTierCode(planId);
    return currentTier === planTierCode;
  };

  const isUpgrade = (planId: string) => {
    const planTierCode = getPlanTierCode(planId);
    const planLevel = tierHierarchy[planTierCode] || 0;
    const currentLevel = getCurrentTierLevel();
    return planLevel > currentLevel;
  };

  const isDowngrade = (planId: string) => {
    const planTierCode = getPlanTierCode(planId);
    const planLevel = tierHierarchy[planTierCode] || 0;
    const currentLevel = getCurrentTierLevel();
    return planLevel < currentLevel && currentLevel > 0;
  };

  const getButtonText = (plan: typeof plans[0]) => {
    if (isCurrentPlan(plan.id)) return "Current Plan";
    if (isUpgrade(plan.id)) return "Upgrade";
    if (isDowngrade(plan.id)) return "Downgrade";
    // For trial/expired users
    return "Get Started";
  };

  const getButtonSubtext = (plan: typeof plans[0]) => {
    if (isDowngrade(plan.id)) return "Takes effect next billing cycle";
    return null;
  };

  const includedFeatures = [
    "AI-generated comments",
    "AI-generated DMs",
    "Community Relevancy Score",
    "Post Relevancy Score",
  ];

  const plans = [
    {
      id: "starter",
      name: "Starter",
      monthlyPrice: 15,
      annualPrice: 11,
      annualTotal: 132,
      annualSavings: 48,
      badge: "7-Day Free Trial",
      badgeStyle: "orange",
      cardStyle: "starter", // orange border
      features: [
        { text: "1", highlight: true, suffix: " business profile" },
        { text: "Up to ", highlight: false, bold: "15", suffix: " subreddits" },
        { text: "Leads refresh ", highlight: false, bold: "twice a day", suffix: "" },
        { text: "3,000", highlight: true, suffix: " leads/month" },
        { text: "Early access to ", highlight: false, bold: "X, TikTok & Instagram", suffix: " (March 2026)" },
      ],
      cta: "Get Started",
    },
    {
      id: "growth",
      name: "Growth",
      monthlyPrice: 39,
      annualPrice: 30,
      annualTotal: 360,
      annualSavings: 108,
      badge: "Most Popular",
      badgeStyle: "white",
      cardStyle: "growth", // orange gradient
      features: [
        { text: "3", highlight: true, suffix: " business profiles" },
        { text: "Up to ", highlight: false, bold: "20", suffix: " subreddits each" },
        { text: "7×24", highlight: true, suffix: " real-time refresh" },
        { text: "9,000", highlight: true, suffix: " leads/month" },
        { text: "Early access to ", highlight: false, bold: "X, TikTok & Instagram", suffix: " (March 2026)" },
      ],
      cta: "Get Started",
    },
    {
      id: "pro",
      name: "Pro",
      monthlyPrice: 99,
      annualPrice: 75,
      annualTotal: 900,
      annualSavings: 288,
      badge: "Best for Teams",
      badgeStyle: "dark",
      cardStyle: "pro", // dark background
      features: [
        { text: "Up to ", highlight: false, bold: "10", suffix: " business profiles" },
        { text: "Unlimited", highlight: true, suffix: " subreddits" },
        { text: "7×24", highlight: true, suffix: " real-time refresh" },
        { text: "30,000", highlight: true, suffix: " leads/month" },
        { text: "Early access to ", highlight: false, bold: "X, TikTok & Instagram", suffix: " (March 2026)" },
      ],
      cta: "Get Started",
    },
  ];

  const handleSubscribe = async (planId: string) => {
    const tierCode = billingPeriod === "monthly"
      ? `${planId.toUpperCase()}_MONTHLY`
      : `${planId.toUpperCase()}_ANNUALLY`;

    setIsLoading(true);
    setError(null);

    try {
      const { checkout_url } = await createCheckoutSession(tierCode);
      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start checkout");
      setIsLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { portal_url } = await createPortalSession();
      // Redirect to Stripe Customer Portal
      window.location.href = portal_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open portal");
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 transition-colors z-10"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="p-6 md:p-8">
          {/* Header - Show upgrade context if present, otherwise show default */}
          {upgradeContext ? (
            <div className="flex items-center gap-3 mb-6 p-4 bg-orange-50 border border-orange-100 rounded-xl">
              <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {UPGRADE_MESSAGES[upgradeContext.reason].title}
                </h2>
                <p className="text-sm text-gray-500">
                  {UPGRADE_MESSAGES[upgradeContext.reason].description(
                    upgradeContext.currentCount,
                    upgradeContext.maxCount
                  )}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {trialActive
                  ? `${trialDaysRemaining} day${trialDaysRemaining !== 1 ? "s" : ""} left in your free trial`
                  : isPaid
                  ? "Manage your subscription"
                  : currentTier === "EXPIRED" || (currentTier === "FREE_TRIAL" && !trialActive)
                  ? "Oops, your free trial has ended. Choose a plan to continue using moreach"
                  : "Choose a plan to continue using moreach"}
              </h2>
            </div>
          )}

          {/* Billing Period Toggle */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center bg-gray-100 rounded-full p-1">
              <button
                onClick={() => setBillingPeriod("annually")}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all flex items-center gap-2 ${
                  billingPeriod === "annually"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Annually
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Save 3 months</span>
              </button>
              <button
                onClick={() => setBillingPeriod("monthly")}
                className={`px-5 py-2 rounded-full text-sm font-semibold transition-all ${
                  billingPeriod === "monthly"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Monthly
              </button>
            </div>
          </div>

          {/* Trial/Expired Status Banner */}
          {currentTier === "EXPIRED" && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <span className="font-semibold text-red-700">Trial Expired</span>
                <p className="text-sm text-red-600">Subscribe to continue monitoring Reddit for leads.</p>
              </div>
            </div>
          )}

          {/* Pricing Cards */}
          <div className="grid md:grid-cols-3 gap-4 md:gap-6">
            {plans.map((plan) => {
              const currentPrice = billingPeriod === "monthly" ? plan.monthlyPrice : plan.annualPrice;
              const isCurrent = isCurrentPlan(plan.id);
              const isRecommended = upgradeContext?.recommendedTier?.toUpperCase() === plan.id.toUpperCase();

              // Card styles based on plan type
              const baseCardClasses = {
                starter: "bg-white border-2 border-orange-300 hover:border-orange-400",
                growth: "bg-gradient-to-br from-orange-500 to-red-500 text-white",
                pro: "bg-gray-900 text-white",
              }[plan.cardStyle];

              // Add ring highlight for recommended plan
              const cardClasses = isRecommended
                ? `${baseCardClasses} ring-4 ring-orange-400 ring-offset-2`
                : baseCardClasses;

              const isGrowth = plan.cardStyle === "growth";
              const isPro = plan.cardStyle === "pro";
              const isDark = isGrowth || isPro;

              return (
                <div
                  key={plan.id}
                  className={`relative rounded-2xl p-6 transition-all hover:shadow-xl flex flex-col ${cardClasses}`}
                >
                  {/* Header with name and badge */}
                  <div className="flex items-start justify-between mb-4">
                    <h3 className={`text-xl font-semibold ${
                      isGrowth ? "text-orange-100" : isPro ? "text-gray-400" : "text-gray-500"
                    }`}>
                      {plan.name}
                    </h3>
                    {(plan.badge || isRecommended) && (
                      <span className={`text-xs font-semibold px-3 py-1 rounded-full ${
                        isRecommended
                          ? "bg-orange-500 text-white"
                          : plan.badgeStyle === "orange"
                          ? "bg-orange-100 text-orange-600"
                          : plan.badgeStyle === "white"
                          ? "bg-white/20 backdrop-blur-sm text-white"
                          : "bg-white/10 backdrop-blur-sm text-gray-300"
                      }`}>
                        {isRecommended ? "Recommended" : plan.badge}
                      </span>
                    )}
                  </div>

                  {/* Price */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-2">
                      {billingPeriod === "annually" && (
                        <span className={`text-2xl font-bold line-through ${
                          isGrowth ? "text-white/50" : isPro ? "text-gray-500" : "text-gray-400"
                        }`}>
                          ${plan.monthlyPrice}
                        </span>
                      )}
                      <span className={`text-5xl font-bold ${isDark ? "text-white" : "text-gray-900"}`}>
                        ${currentPrice}
                      </span>
                      <span className={isGrowth ? "text-orange-100" : isPro ? "text-gray-400" : "text-gray-500"}>
                        /month
                      </span>
                    </div>
                    {billingPeriod === "annually" && (
                      <p className={`text-sm font-medium mt-1 ${
                        isGrowth ? "text-white" : isPro ? "text-green-400" : "text-green-600"
                      }`}>
                        Billed ${plan.annualTotal}/year (Save ${plan.annualSavings})
                      </p>
                    )}
                  </div>

                  {/* Variable Features */}
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <svg
                          className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                            isGrowth ? "text-white" : isPro ? "text-green-400" : "text-green-500"
                          }`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span className={isDark ? "text-white" : "text-gray-700"}>
                          {feature.bold ? (
                            <>
                              {feature.text}
                              <strong>{feature.bold}</strong>
                              {feature.suffix}
                            </>
                          ) : (
                            <>
                              <strong>{feature.text}</strong>
                              {feature.suffix}
                            </>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>

                  {/* Included Features */}
                  <div className={`border-t pt-6 mt-auto ${
                    isGrowth ? "border-white/20" : isPro ? "border-gray-700" : "border-gray-200"
                  }`}>
                    <p className={`text-xs font-semibold uppercase tracking-wide mb-3 ${
                      isGrowth ? "text-white/60" : isPro ? "text-gray-500" : "text-gray-400"
                    }`}>
                      Included
                    </p>
                    <ul className="space-y-2">
                      {includedFeatures.map((feature, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-sm">
                          <svg
                            className={`w-4 h-4 ${
                              isGrowth ? "text-white/60" : isPro ? "text-gray-500" : "text-gray-400"
                            }`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                          </svg>
                          <span className={isGrowth ? "text-white/80" : isPro ? "text-gray-400" : "text-gray-600"}>
                            {feature}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* CTA Button */}
                  <div className="mt-6">
                    <button
                      onClick={() => handleSubscribe(plan.id)}
                      disabled={isCurrent || isLoading}
                      className={`w-full py-4 rounded-xl font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                        isCurrent
                          ? isDark
                            ? "bg-white/20 text-white/60"
                            : "bg-gray-100 text-gray-400"
                          : isDowngrade(plan.id)
                          ? isDark
                            ? "bg-white/10 hover:bg-white/20 text-white/80 border border-white/20"
                            : "bg-gray-50 hover:bg-gray-100 text-gray-600 border border-gray-200"
                          : isGrowth
                          ? "bg-white hover:bg-orange-50 text-orange-600"
                          : isPro
                          ? "bg-white hover:bg-gray-100 text-gray-900"
                          : "bg-gray-900 hover:bg-gray-800 text-white"
                      }`}
                    >
                      {isLoading ? "Loading..." : getButtonText(plan)}
                    </button>
                    {getButtonSubtext(plan) && (
                      <p className={`text-xs text-center mt-2 ${isDark ? "text-white/50" : "text-gray-400"}`}>
                        {getButtonSubtext(plan)}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              All plans include a 7-day money-back guarantee.{" "}
              <button className="text-gray-700 underline hover:text-gray-900">
                Contact support
              </button>{" "}
              if you have questions.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Manage Subscription (for paid users) */}
          {isPaid && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={handleManageSubscription}
                disabled={isLoading}
                className="w-full py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Loading..." : "Manage Subscription in Stripe"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
