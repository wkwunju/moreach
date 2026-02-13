"use client";

import { useState, useEffect, useCallback, Suspense, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  createRedditCampaign,
  discoverSubreddits,
  selectSubreddits,
  fetchRedditCampaigns,
  fetchRedditLeads,
  updateLeadStatus,
  pauseCampaign,
  resumeCampaign,
  runCampaignPoll,
  generateLeadSuggestions,
  fetchCampaignSubreddits,
  deleteCampaign,
  checkCanCreateProfile,
  checkSubredditLimit,
  getPlanLimits,
  getPollStatus,
  analyzeUrl,
  type SSEProgressEvent,
  type SSELeadEvent,
  type SSECompleteEvent,
  type PollTaskStatus,
} from "@/lib/api";
import type { RedditCampaign, SubredditInfo, RedditLead } from "@/lib/types";
import ProtectedRoute from "@/components/ProtectedRoute";
import DashboardLayout from "@/components/DashboardLayout";
import UserMenu from "@/components/UserMenu";
import { getUser, logout, getTrialDaysRemaining, isTrialActive, type User } from "@/lib/auth";
import BillingDialog from "@/components/BillingDialog";
// UpgradeDialog replaced - now using BillingDialog with upgradeContext

type Step = "campaigns" | "create" | "discover" | "leads";

// Loading messages for subreddit discovery
const DISCOVERY_MESSAGES = [
  { text: "Analyzing your business description...", icon: "analyze" },
  { text: "Understanding your target audience...", icon: "audience" },
  { text: "Searching Reddit communities...", icon: "search" },
  { text: "Evaluating community relevance...", icon: "evaluate" },
  { text: "Calculating match scores...", icon: "calculate" },
  { text: "Ranking subreddits for you...", icon: "rank" },
];

// Animated loading component for discovery
function DiscoveryLoadingState() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    // Cycle through messages every 3 seconds with smooth transition
    const messageInterval = setInterval(() => {
      // Start fade out
      setIsTransitioning(true);
      // After fade out completes, change message and fade in
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % DISCOVERY_MESSAGES.length);
        setIsTransitioning(false);
      }, 400); // Match the fade-out duration
    }, 3000);

    // Animate progress bar
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) return prev; // Cap at 95% until done
        return prev + Math.random() * 3;
      });
    }, 200);

    return () => {
      clearInterval(messageInterval);
      clearInterval(progressInterval);
    };
  }, []);

  const currentMessage = DISCOVERY_MESSAGES[currentIndex];

  const getIcon = (iconType: string) => {
    switch (iconType) {
      case "analyze":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        );
      case "audience":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        );
      case "search":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        );
      case "evaluate":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        );
      case "calculate":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case "rank":
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="py-16 px-8">
      <div className="max-w-md mx-auto">
        {/* Animated Icon */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            {/* Pulsing background */}
            <div className="absolute inset-0 bg-orange-100 rounded-full animate-ping opacity-25" />
            {/* Icon container */}
            <div className="relative w-16 h-16 bg-gradient-to-br from-orange-500 to-orange-600 rounded-full flex items-center justify-center text-white shadow-lg">
              <div className="animate-pulse">
                {getIcon(currentMessage.icon)}
              </div>
            </div>
          </div>
        </div>

        {/* Message with smooth fade transition */}
        <div className="text-center mb-8 h-16">
          <p
            key={currentIndex}
            className={`text-lg font-medium text-gray-900 transition-all duration-400 ease-in-out ${
              isTransitioning ? "opacity-0 translate-y-2" : "opacity-100 translate-y-0"
            }`}
          >
            {currentMessage.text}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            This may take a moment...
          </p>
        </div>

        {/* Progress bar */}
        <div className="mb-6">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-orange-400 to-orange-500 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Step indicators */}
        <div className="flex justify-center gap-2">
          {DISCOVERY_MESSAGES.map((_, idx) => (
            <div
              key={idx}
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                idx === currentIndex
                  ? "bg-orange-500 scale-125"
                  : idx < currentIndex
                  ? "bg-orange-400"
                  : "bg-gray-300"
              }`}
            />
          ))}
        </div>
      </div>

      {/* CSS for custom transition duration */}
      <style jsx>{`
        .duration-400 {
          transition-duration: 400ms;
        }
      `}</style>
    </div>
  );
}

// Helper function to display time ago
function getTimeAgo(timestamp: number): string {
  const now = Date.now() / 1000;
  const diff = now - timestamp;

  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)} days ago`;
  return `${Math.floor(diff / 2592000)} months ago`;
}

// Subscription status card component
function SubscriptionStatusCard({
  user,
  onSubscribe,
}: {
  user: User;
  onSubscribe: () => void;
}) {
  const trialActive = isTrialActive(user);
  const trialDays = getTrialDaysRemaining(user);
  const currentTier = user.subscription_tier;

  // Determine subscription status
  // Support both old format (MONTHLY, ANNUALLY) and new format (STARTER_MONTHLY, etc.)
  const isPaid = currentTier === "MONTHLY" ||
    currentTier === "ANNUALLY" ||
    currentTier?.startsWith("STARTER") ||
    currentTier?.startsWith("GROWTH") ||
    currentTier?.startsWith("PRO");

  const isExpired = !user.is_admin && (currentTier === "EXPIRED" ||
    (currentTier === "FREE_TRIAL" && !trialActive));

  // Get display info based on status
  const getStatusInfo = () => {
    if (isPaid) {
      // Determine plan name and billing cycle
      let tierName = "Pro";
      let billingCycle = "Monthly";

      if (currentTier === "MONTHLY") {
        tierName = "Pro";
        billingCycle = "Monthly";
      } else if (currentTier === "ANNUALLY") {
        tierName = "Pro";
        billingCycle = "Annual";
      } else if (currentTier?.includes("_")) {
        tierName = currentTier.split("_")[0];
        tierName = tierName.charAt(0) + tierName.slice(1).toLowerCase();
        billingCycle = currentTier.includes("ANNUALLY") ? "Annual" : "Monthly";
      }

      return {
        title: `${tierName} Plan`,
        subtitle: `${billingCycle} subscription active`,
        showButton: false,
        bgColor: "bg-green-50",
        borderColor: "border-green-200",
        iconColor: "text-green-500",
        titleColor: "text-green-700",
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
    }

    if (trialActive) {
      return {
        title: "Free Trial Active",
        subtitle: `${trialDays} day${trialDays !== 1 ? "s" : ""} left in trial. Subscribe to keep real-time monitoring active.`,
        showButton: true,
        bgColor: "bg-orange-50",
        borderColor: "border-orange-200",
        iconColor: "text-orange-500",
        titleColor: "text-orange-700",
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
    }

    if (isExpired) {
      return {
        title: "Trial Expired",
        subtitle: "Subscribe to continue monitoring Reddit for leads.",
        showButton: true,
        bgColor: "bg-red-50",
        borderColor: "border-red-200",
        iconColor: "text-red-500",
        titleColor: "text-red-700",
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        ),
      };
    }

    // Fallback: show trial status for FREE_TRIAL or unknown tiers
    return {
      title: "Free Trial",
      subtitle: "Subscribe to unlock all features.",
      showButton: true,
      bgColor: "bg-orange-50",
      borderColor: "border-orange-200",
      iconColor: "text-orange-500",
      titleColor: "text-orange-700",
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    };
  };

  const status = getStatusInfo();

  return (
    <div className="px-4 pb-4">
      <div className={`p-3 ${status.bgColor} border ${status.borderColor} rounded-xl`}>
        <div className="flex items-center gap-2 mb-1">
          <span className={status.iconColor}>{status.icon}</span>
          <span className={`text-sm font-semibold ${status.titleColor}`}>{status.title}</span>
        </div>
        <p className="text-xs text-gray-600 mb-3">{status.subtitle}</p>
        {status.showButton && (
          <button
            onClick={onSubscribe}
            className="w-full py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
            Subscribe Now
          </button>
        )}
      </div>
    </div>
  );
}

function RedditPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [step, setStep] = useState<Step>("campaigns");
  const [campaigns, setCampaigns] = useState<RedditCampaign[]>([]);
  const [currentCampaign, setCurrentCampaign] = useState<RedditCampaign | null>(null);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [subreddits, setSubreddits] = useState<SubredditInfo[]>([]);
  const [selectedSubreddits, setSelectedSubreddits] = useState<Map<string, SubredditInfo>>(new Map());
  const [leads, setLeads] = useState<RedditLead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Form states
  const [businessDescription, setBusinessDescription] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [analyzingUrl, setAnalyzingUrl] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>("NEW");
  
  // Inbox view states
  const [selectedLead, setSelectedLead] = useState<RedditLead | null>(null);
  const [selectedSubreddit, setSelectedSubreddit] = useState<string>("all");
  
  // Lead counts by status
  const [leadCounts, setLeadCounts] = useState({ new: 0, contacted: 0 });
  
  // Sort order state
  const [sortOrder, setSortOrder] = useState<"relevancy" | "time">("relevancy");

  // Helper function to get the first lead from a sorted list
  const getFirstSortedLead = useCallback((leadsArray: RedditLead[], order: "relevancy" | "time" = "relevancy"): RedditLead | null => {
    if (leadsArray.length === 0) return null;

    const sorted = [...leadsArray].sort((a, b) => {
      if (order === "relevancy") {
        const scoreA = a.relevancy_score || 0;
        const scoreB = b.relevancy_score || 0;
        if (scoreB !== scoreA) return scoreB - scoreA;
        return (b.created_utc || 0) - (a.created_utc || 0);
      } else {
        const timeA = a.created_utc || 0;
        const timeB = b.created_utc || 0;
        if (timeB !== timeA) return timeB - timeA;
        return (b.relevancy_score || 0) - (a.relevancy_score || 0);
      }
    });

    return sorted[0];
  }, []);
  
  // Add Subreddit modal states
  const [showAddSubredditModal, setShowAddSubredditModal] = useState(false);
  const [trackedSubreddits, setTrackedSubreddits] = useState<SubredditInfo[]>([]);
  const [recommendedSubreddits, setRecommendedSubreddits] = useState<SubredditInfo[]>([]);
  const [loadingTracked, setLoadingTracked] = useState(false);
  const [loadingRecommended, setLoadingRecommended] = useState(false);
  const [selectedNewSubreddits, setSelectedNewSubreddits] = useState<Set<string>>(new Set());
  
  // Delete campaign modal states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [campaignToDelete, setCampaignToDelete] = useState<RedditCampaign | null>(null);

  // Success dialog state
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);

  // Streaming progress states
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamProgress, setStreamProgress] = useState<SSEProgressEvent | null>(null);
  const [streamingLeads, setStreamingLeads] = useState<SSELeadEvent[]>([]);
  const [streamComplete, setStreamComplete] = useState<SSECompleteEvent | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // Auto-refresh leads when on leads page (to show newly scored leads)
  useEffect(() => {
    if (step !== "leads" || !currentCampaign || isStreaming) return;

    const refreshLeads = async () => {
      try {
        const data = await fetchRedditLeads(currentCampaign.id, filterStatus);
        // Only update if counts changed (new leads scored)
        if (data.new_leads !== leadCounts.new || data.contacted_leads !== leadCounts.contacted || data.leads.length !== leads.length) {
          setLeads(data.leads);
          setLeadCounts({
            new: data.new_leads,
            contacted: data.contacted_leads
          });
          // Keep current selection if still in list, otherwise select first
          if (selectedLead && !data.leads.find((l: RedditLead) => l.id === selectedLead.id)) {
            setSelectedLead(getFirstSortedLead(data.leads, sortOrder));
          }
        }
      } catch (err) {
        console.error("Failed to refresh leads:", err);
      }
    };

    // Poll every 5 seconds
    const intervalId = setInterval(refreshLeads, 5000);
    return () => clearInterval(intervalId);
  }, [step, currentCampaign, filterStatus, isStreaming, leadCounts.new, leadCounts.contacted, leads.length, selectedLead, sortOrder]);

  // Subreddit display states
  const [showMoreHighScore, setShowMoreHighScore] = useState(false);
  const [showLowScore, setShowLowScore] = useState(false);

  // User info state
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [showBillingDialog, setShowBillingDialog] = useState(false);

  // Upgrade context for BillingDialog (when showing upgrade prompts)
  const [upgradeContext, setUpgradeContext] = useState<{
    reason: "profile_limit" | "subreddit_limit";
    currentCount: number;
    maxCount: number;
    recommendedTier: string;
  } | undefined>(undefined);

  // Plan limits - will be fetched from API
  const [maxSubredditSelection, setMaxSubredditSelection] = useState(15);
  const MAX_SUBREDDIT_SELECTION = maxSubredditSelection;

  // Ref to prevent double API calls in StrictMode
  const initPageCalledRef = useRef(false);

  // Ref to skip pushState when handling popstate (browser back/forward)
  const isPopstateRef = useRef(false);

  // Campaign settings menu state
  const [openSettingsMenu, setOpenSettingsMenu] = useState<number | null>(null);

  // Resizable panel states
  // 使用黄金分割比例 (0.618:1) - 详情面板占 61.8%（宽），列表占 38.2%（窄）
  const calculateGoldenRatioWidth = () => {
    const sidebarWidth = 256; // 左侧栏宽度
    const availableWidth = window.innerWidth - sidebarWidth;
    const goldenRatio = 1 / 1.618; // ≈ 0.618
    // 详情面板占 61.8%（更宽），列表占 38.2%（更窄）
    return availableWidth * goldenRatio;
  };
  
  const [detailPanelWidth, setDetailPanelWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      return calculateGoldenRatioWidth();
    }
    return 650; // SSR fallback
  });
  const [isResizing, setIsResizing] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [isXlScreen, setIsXlScreen] = useState(false);

  // Track desktop/mobile and xl breakpoint for responsive width
  useEffect(() => {
    const checkBreakpoints = () => {
      setIsDesktop(window.innerWidth >= 1024);
      setIsXlScreen(window.innerWidth >= 1280);
    };
    checkBreakpoints();
    window.addEventListener('resize', checkBreakpoints);
    return () => window.removeEventListener('resize', checkBreakpoints);
  }, []);

  // Helper to update URL without full navigation
  const updateURL = useCallback((newStep: Step, campaignId?: number) => {
    const params = new URLSearchParams();
    if (newStep !== "campaigns") {
      params.set("view", newStep);
    }
    if (campaignId) {
      params.set("id", campaignId.toString());
    }
    const newUrl = params.toString() ? `/reddit?${params.toString()}` : "/reddit";
    if (isPopstateRef.current) {
      // Browser back/forward triggered this - don't push new entry
      isPopstateRef.current = false;
    } else {
      window.history.pushState({ step: newStep, campaignId }, "", newUrl);
    }
  }, []);

  // Load campaigns and restore state from URL on mount
  useEffect(() => {
    // Prevent double API calls in React StrictMode
    if (initPageCalledRef.current) return;
    initPageCalledRef.current = true;

    async function initPage() {
      try {
        setLoading(true);

        // Fetch plan limits first
        try {
          const limits = await getPlanLimits();
          setMaxSubredditSelection(limits.max_subreddits_per_profile);
        } catch (err) {
          console.error("Failed to fetch plan limits:", err);
          // Keep default of 15
        }

        const data = await fetchRedditCampaigns();
        setCampaigns(data);

        // Check for any running poll tasks and resume progress display
        for (const campaign of data) {
          if (campaign.status === "ACTIVE") {
            try {
              const pollStatus = await getPollStatus(campaign.id);
              if (pollStatus.status === "running") {
                // Resume showing progress for this running task
                setIsStreaming(true);
                setStreamProgress({
                  phase: pollStatus.phase as "fetching" | "scoring" | "suggestions",
                  current: pollStatus.current,
                  total: pollStatus.total,
                  message: pollStatus.message,
                });
                // Start polling for updates
                const cleanup = runCampaignPoll(
                  campaign.id,
                  (status: PollTaskStatus) => {
                    setStreamProgress({
                      phase: status.phase as "fetching" | "scoring" | "suggestions",
                      current: status.current,
                      total: status.total,
                      message: status.message,
                    });
                    if (status.leads_created > 0) {
                      setStreamingLeads(status.leads.map(id => ({
                        id,
                        title: "",
                        relevancy_score: 0,
                        subreddit_name: "",
                        has_suggestions: false,
                      })));
                    }
                  },
                  (status: PollTaskStatus) => {
                    const summary = status.summary || {
                      total_leads: status.leads_created,
                      total_posts_fetched: status.total,
                      subreddits_polled: 0,
                    };
                    setStreamComplete(summary);
                    setIsStreaming(false);
                    // Refresh campaigns
                    loadCampaigns();
                  },
                  (error: Error) => {
                    setError(error.message || "Failed to run radar");
                    setIsStreaming(false);
                  }
                );
                break; // Only handle one running poll at a time
              }
            } catch (e) {
              // Ignore errors when checking poll status
              console.error("Error checking poll status:", e);
            }
          }
        }

        // Restore state from URL params
        const view = searchParams.get("view") as Step | null;
        const campaignId = searchParams.get("id");

        if (view && campaignId) {
          const campaign = data.find((c: RedditCampaign) => c.id === parseInt(campaignId));
          if (campaign) {
            setCurrentCampaign(campaign);
            if (view === "leads") {
              // Load leads for this campaign
              const leadsData = await fetchRedditLeads(campaign.id, "NEW");
              setLeads(leadsData.leads);
              setLeadCounts({
                new: leadsData.new_leads,
                contacted: leadsData.contacted_leads
              });
              // Select first lead based on sort order (default: relevancy)
              setSelectedLead(getFirstSortedLead(leadsData.leads, "relevancy"));
              setStep("leads");
            } else if (view === "discover") {
              const discovered = await discoverSubreddits(campaign.id);
              setSubreddits(discovered);
              setStep("discover");
            }
          }
        } else if (view === "create") {
          setStep("create");
        }

        setInitialLoadDone(true);

        // Set initial history state so popstate can restore correctly
        const initialStep = (view as Step) || "campaigns";
        const initialCampaignId = campaignId ? parseInt(campaignId) : undefined;
        window.history.replaceState({ step: initialStep, campaignId: initialCampaignId }, "", window.location.href);
      } catch (err) {
        setError("Failed to load radars");
      } finally {
        setLoading(false);
      }
    }
    initPage();
  }, [searchParams]);

  // Update URL when step or campaign changes (after initial load)
  useEffect(() => {
    if (initialLoadDone) {
      updateURL(step, currentCampaign?.id);
    }
  }, [step, currentCampaign?.id, initialLoadDone, updateURL]);

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = async (event: PopStateEvent) => {
      isPopstateRef.current = true;
      const state = event.state;
      if (state?.step) {
        // Restore from pushState data
        if (state.step === "campaigns") {
          setStep("campaigns");
          setCurrentCampaign(null);
        } else if (state.step === "leads" && state.campaignId) {
          const campaign = campaigns.find((c) => c.id === state.campaignId);
          if (campaign) {
            setCurrentCampaign(campaign);
            const leadsData = await fetchRedditLeads(campaign.id, "NEW");
            setLeads(leadsData.leads);
            setLeadCounts({ new: leadsData.new_leads, contacted: leadsData.contacted_leads });
            setSelectedLead(getFirstSortedLead(leadsData.leads, "relevancy"));
            setStep("leads");
          } else {
            setStep("campaigns");
          }
        } else {
          setStep(state.step);
        }
      } else {
        // No state - we're at the initial /reddit page
        setStep("campaigns");
        setCurrentCampaign(null);
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [campaigns, getFirstSortedLead]);

  // Load user info on mount
  useEffect(() => {
    const user = getUser();
    setCurrentUser(user);
  }, []);

  // Calculate isExpired at component level for use in handlers
  const currentTier = currentUser?.subscription_tier;
  const trialActive = isTrialActive(currentUser);
  const isAdmin = currentUser?.is_admin ?? false;
  const isExpired = !isAdmin && (currentTier === "EXPIRED" ||
    (currentTier === "FREE_TRIAL" && !trialActive));

  async function loadCampaigns() {
    try {
      setLoading(true);
      const data = await fetchRedditCampaigns();
      setCampaigns(data);
    } catch (err) {
      setError("Failed to load radars");
    } finally {
      setLoading(false);
    }
  }

  // Check if user can create a new profile and show upgrade dialog if not
  async function handleNewRadarClick() {
    try {
      const result = await checkCanCreateProfile();
      if (result.allowed) {
        setStep("create");
      } else {
        // Show billing dialog with upgrade context
        setUpgradeContext({
          reason: "profile_limit",
          currentCount: result.current_count,
          maxCount: result.max_count,
          recommendedTier: result.upgrade_to || "GROWTH",
        });
        setShowBillingDialog(true);
      }
    } catch (err) {
      // If check fails, allow creation (fail open) and let backend handle it
      console.error("Failed to check profile limit:", err);
      setStep("create");
    }
  }

  async function handleCreateCampaign() {
    if (!businessDescription.trim()) {
      setError("Please describe your business");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const campaign = await createRedditCampaign(businessDescription);
      setCurrentCampaign(campaign);
      setStep("discover");

      // Auto-discover subreddits
      const discovered = await discoverSubreddits(campaign.id);
      setSubreddits(discovered);
      // Reset collapse states for new discovery
      setShowMoreHighScore(false);
      setShowLowScore(false);
    } catch (err) {
      setError("Failed to create radar");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectSubreddits() {
    if (!currentCampaign || selectedSubreddits.size === 0) {
      setError("Please select at least one subreddit");
      return;
    }

    try {
      setLoading(true);
      setError("");
      await selectSubreddits(currentCampaign.id, Array.from(selectedSubreddits.values()));
      loadCampaigns();
      setShowSuccessDialog(true);
    } catch (err) {
      setError("Failed to activate radar");
    } finally {
      setLoading(false);
    }
  }

  async function handleViewLeads(campaign: RedditCampaign, status?: string) {
    // Check if trial expired - show billing dialog instead
    if (isExpired) {
      setShowBillingDialog(true);
      return;
    }

    try {
      setLoading(true);
      setCurrentCampaign(campaign);
      // Use provided status or fall back to filterStatus
      const statusToUse = status !== undefined ? status : filterStatus;
      const data = await fetchRedditLeads(campaign.id, statusToUse);
      setLeads(data.leads);
      setLeadCounts({
        new: data.new_leads,
        contacted: data.contacted_leads
      });
      // Select first lead based on current sort order
      setSelectedLead(getFirstSortedLead(data.leads, sortOrder));
      setStep("leads");
    } catch (err) {
      setError("Failed to load leads");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdateStatus(leadId: number, status: string): Promise<RedditLead[]> {
    try {
      await updateLeadStatus(leadId, status);
      // Refresh leads and counts
      if (currentCampaign) {
        const data = await fetchRedditLeads(currentCampaign.id, filterStatus);
        setLeads(data.leads);
        setLeadCounts({
          new: data.new_leads,
          contacted: data.contacted_leads
        });
        return data.leads;
      }
      return [];
    } catch (err) {
      setError("Failed to update lead status");
      return [];
    }
  }

  async function handleCopyAndComment(lead: RedditLead) {
    try {
      // Copy suggested comment to clipboard
      await navigator.clipboard.writeText(lead.suggested_comment || '');

      // Open Reddit post in new tab
      window.open(lead.post_url, '_blank');

      // Update status to "Contacted" - returns refreshed leads
      const updatedLeads = await handleUpdateStatus(lead.id, "CONTACTED");

      // Select first lead from updated list
      setSelectedLead(getFirstSortedLead(updatedLeads, sortOrder));
    } catch (err) {
      setError("Failed to copy comment");
    }
  }

  async function handleCopyAndDM(lead: RedditLead) {
    try {
      // Copy suggested DM to clipboard
      await navigator.clipboard.writeText(lead.suggested_dm || '');

      // Open Reddit user page in new tab
      const userPageUrl = `https://www.reddit.com/user/${lead.author}`;
      window.open(userPageUrl, '_blank');

      // Update status to "Contacted" - returns refreshed leads
      const updatedLeads = await handleUpdateStatus(lead.id, "CONTACTED");

      // Select first lead from updated list
      setSelectedLead(getFirstSortedLead(updatedLeads, sortOrder));
    } catch (err) {
      setError("Failed to copy DM");
    }
  }

  async function handleToggleCampaign(campaign: RedditCampaign) {
    try {
      if (campaign.status === "ACTIVE") {
        await pauseCampaign(campaign.id);
      } else {
        await resumeCampaign(campaign.id);
      }
      loadCampaigns();
    } catch (err) {
      setError("Failed to toggle radar");
    }
  }

  async function handleRunNow(campaign: RedditCampaign) {
    // Use background polling version - continues even if page is closed
    setIsStreaming(true);
    setStreamProgress(null);
    setStreamingLeads([]);
    setStreamComplete(null);
    setError("");

    const cleanup = runCampaignPoll(
      campaign.id,
      // onProgress
      (status: PollTaskStatus) => {
        setStreamProgress({
          phase: status.phase as "fetching" | "scoring" | "suggestions",
          current: status.current,
          total: status.total,
          message: status.message,
        });
        // Update leads count from status
        if (status.leads_created > 0) {
          // Create minimal lead events from the IDs we have
          setStreamingLeads(status.leads.map(id => ({
            id,
            title: "",
            relevancy_score: 0,
            subreddit_name: "",
            has_suggestions: false,
          })));
        }
      },
      // onComplete
      (status: PollTaskStatus) => {
        const summary = status.summary || {
          total_leads: status.leads_created,
          total_posts_fetched: status.total,
          subreddits_polled: 0,
        };
        setStreamComplete(summary);
        setIsStreaming(false);
        // Refresh campaigns and leads
        loadCampaigns();
        if (currentCampaign?.id === campaign.id) {
          handleViewLeads(campaign);
        }
      },
      // onError
      (error: Error) => {
        setError(error.message || "Failed to run radar");
        setIsStreaming(false);
      }
    );

    // Store cleanup function (could be used for cancel button)
    return cleanup;
  }

  // On-demand suggestion loading when selecting a lead
  async function handleSelectLead(lead: RedditLead) {
    setSelectedLead(lead);

    // Check if suggestions need to be loaded
    if (!lead.has_suggestions && !lead.suggested_comment && !lead.suggested_dm) {
      setLoadingSuggestions(true);
      try {
        const suggestions = await generateLeadSuggestions(lead.id);
        // Update the lead in state with new suggestions
        const updatedLead = {
          ...lead,
          suggested_comment: suggestions.suggested_comment,
          suggested_dm: suggestions.suggested_dm,
          has_suggestions: true,
        };
        setSelectedLead(updatedLead);
        // Also update in leads array
        setLeads((prev) =>
          prev.map((l) => (l.id === lead.id ? updatedLead : l))
        );
      } catch (err) {
        console.error("Failed to generate suggestions:", err);
      } finally {
        setLoadingSuggestions(false);
      }
    }
  }

  function handleDeleteCampaign(campaign: RedditCampaign) {
    setCampaignToDelete(campaign);
    setShowDeleteModal(true);
  }

  async function confirmDeleteCampaign() {
    if (!campaignToDelete) return;

    try {
      setLoading(true);
      setError("");
      await deleteCampaign(campaignToDelete.id);
      loadCampaigns();
      setShowDeleteModal(false);
      setCampaignToDelete(null);
    } catch (err: any) {
      setError(err.message || "Failed to delete radar");
    } finally {
      setLoading(false);
    }
  }

  function toggleSubreddit(subreddit: SubredditInfo) {
    const newMap = new Map(selectedSubreddits);
    if (newMap.has(subreddit.name)) {
      newMap.delete(subreddit.name);
    } else {
      // Enforce max selection limit
      if (newMap.size >= MAX_SUBREDDIT_SELECTION) {
        // Show billing dialog with upgrade context
        const tier = currentUser?.subscription_tier || "FREE_TRIAL";
        let recommendedTier = "GROWTH";
        if (tier.includes("GROWTH")) {
          recommendedTier = "PRO";
        } else if (tier.includes("PRO")) {
          // Already at max tier, still show dialog but no recommendation
          recommendedTier = "PRO";
        }
        setUpgradeContext({
          reason: "subreddit_limit",
          currentCount: newMap.size + 1,
          maxCount: MAX_SUBREDDIT_SELECTION,
          recommendedTier,
        });
        setShowBillingDialog(true);
        return;
      }
      newMap.set(subreddit.name, subreddit);
    }
    setSelectedSubreddits(newMap);
  }

  async function handleOpenAddSubreddit() {
    if (!currentCampaign) return;
    
    setShowAddSubredditModal(true);
    setLoadingTracked(true);
    setLoadingRecommended(true);

    // Fetch tracked and recommended in parallel with independent loading states
    const trackedPromise = fetchCampaignSubreddits(currentCampaign.id);

    trackedPromise
      .then((tracked) => {
        setTrackedSubreddits(tracked);
        setLoadingTracked(false);
      })
      .catch(() => {
        setError("Failed to load tracked subreddits");
        setLoadingTracked(false);
      });

    Promise.all([trackedPromise, discoverSubreddits(currentCampaign.id)])
      .then(([tracked, recommended]) => {
        const trackedNames = new Set(tracked.map(s => s.name));
        setRecommendedSubreddits(recommended.filter(s => !trackedNames.has(s.name)));
        setLoadingRecommended(false);
      })
      .catch(() => {
        setError("Failed to load recommended subreddits");
        setLoadingRecommended(false);
      });
  }

  async function handleAddSelectedSubreddits() {
    if (!currentCampaign || selectedNewSubreddits.size === 0) return;
    
    try {
      setLoading(true);
      
      // Get full subreddit info for selected ones
      const subredditsToAdd = recommendedSubreddits.filter(s => 
        selectedNewSubreddits.has(s.name)
      );
      
      // Combine with existing tracked subreddits
      const allSubreddits = [...trackedSubreddits, ...subredditsToAdd];
      
      await selectSubreddits(currentCampaign.id, allSubreddits);
      
      setShowAddSubredditModal(false);
      setSelectedNewSubreddits(new Set());
      
      // Refresh leads to show new subreddits
      const data = await fetchRedditLeads(currentCampaign.id, filterStatus);
      setLeads(data.leads);
    } catch (err) {
      setError("Failed to add subreddits");
    } finally {
      setLoading(false);
    }
  }

  function toggleNewSubreddit(name: string) {
    const newSet = new Set(selectedNewSubreddits);
    if (newSet.has(name)) {
      newSet.delete(name);
    } else {
      newSet.add(name);
    }
    setSelectedNewSubreddits(newSet);
  }

  // Handle resizing
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  // 监听窗口大小变化，自动调整为黄金分割比例
  useEffect(() => {
    const handleResize = () => {
      if (!isResizing) {
        setDetailPanelWidth(calculateGoldenRatioWidth());
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isResizing]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      // 计算新宽度 (从右边缘到鼠标位置)
      const newWidth = window.innerWidth - e.clientX;
      
      // 限制最小和最大宽度
      const minWidth = 300; // 最小宽度
      const maxWidth = 800; // 最大宽度
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setDetailPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  return (
    <ProtectedRoute>
      <DashboardLayout hideSidebar={step === "leads"}>
        {/* Wrapper for non-leads views */}
        {step !== "leads" && (
          <div className="p-4 sm:p-6">
            <div className="max-w-6xl mx-auto">
              {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  {error}
                </div>
              )}

              {/* Step: Radars List */}
              {step === "campaigns" && (
          <div>
            {/* Page Header Card */}
            <div className="bg-white rounded-xl p-3 sm:p-5 mb-4 sm:mb-5 shadow-sm border border-gray-100">
              <div className="flex items-center gap-2.5 sm:gap-3">
                {/* Reddit Logo */}
                <img
                  src="https://www.redditstatic.com/desktop2x/img/favicon/android-icon-192x192.png"
                  alt="Reddit"
                  className="w-8 h-8 sm:w-9 sm:h-9 flex-shrink-0"
                />
                <div>
                  <h1 className="text-lg sm:text-xl font-bold text-gray-900">Reddit Lead Generation</h1>
                  <p className="text-gray-400 mt-0.5 text-xs sm:text-sm">
                    AI-powered lead discovery from Reddit
                  </p>
                </div>
              </div>
            </div>

            {/* Your Radars Section */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100">
              {/* Section Header */}
              <div className="px-3 sm:px-5 py-3 sm:py-3.5 border-b border-gray-100 flex flex-col sm:flex-row gap-2 sm:justify-between sm:items-center bg-gray-50/50">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-sm sm:text-base font-semibold text-gray-900">Your Radars</h2>
                    <p className="text-xs text-gray-500">{campaigns.length} active radar{campaigns.length !== 1 ? 's' : ''}</p>
                  </div>
                </div>
                <button
                  onClick={handleNewRadarClick}
                  className="w-full sm:w-auto px-3 sm:px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors font-medium flex items-center justify-center gap-1.5 shadow-sm text-xs sm:text-sm"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                  </svg>
                  New Radar
                </button>
              </div>

              {/* Radars Content */}
              <div className="p-3 sm:p-4 pb-4 sm:pb-5">
                {loading ? (
                  <div className="text-center py-10">
                    <div className="inline-flex items-center gap-2 text-gray-500">
                      <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      <span className="text-sm">Loading your radars...</span>
                    </div>
                  </div>
                ) : campaigns.length === 0 ? (
                  <div className="text-center py-10">
                    <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <p className="text-gray-600 mb-1 font-medium text-sm">No radars yet</p>
                    <p className="text-gray-400 text-xs mb-4">Create your first radar to start discovering leads</p>
                    <button
                      onClick={handleNewRadarClick}
                      className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors font-medium text-sm"
                    >
                      Create Your First Radar
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {campaigns.map((campaign) => (
                      <div
                        key={campaign.id}
                        className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4 hover:border-gray-300 hover:shadow-md transition-all duration-200"
                      >
                        {/* Header: Status Badge + Actions */}
                        <div className="flex justify-between items-center mb-2">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${
                              campaign.status === "ACTIVE"
                                ? "bg-emerald-100 text-emerald-700"
                                : campaign.status === "DISCOVERING"
                                ? "bg-gray-900 text-white"
                                : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {campaign.status}
                          </span>
                          {/* Action Buttons */}
                          <div className="flex gap-1.5 items-center flex-shrink-0">
                            <button
                              onClick={() => handleViewLeads(campaign)}
                              className="px-3 sm:px-4 py-1.5 sm:py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors font-medium text-xs"
                            >
                              View Leads
                            </button>
                            {/* Settings dropdown */}
                            <div className="relative">
                              <button
                                onClick={() => setOpenSettingsMenu(openSettingsMenu === campaign.id ? null : campaign.id)}
                                className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors"
                                title="Radar settings"
                              >
                                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                                </svg>
                              </button>
                              {openSettingsMenu === campaign.id && (
                                <>
                                  {/* Backdrop to close menu */}
                                  <div
                                    className="fixed inset-0 z-10"
                                    onClick={() => setOpenSettingsMenu(null)}
                                  />
                                  {/* Dropdown menu */}
                                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 z-20 overflow-hidden">
                                    <button
                                      onClick={() => {
                                        handleToggleCampaign(campaign);
                                        setOpenSettingsMenu(null);
                                      }}
                                      className="w-full px-4 py-3 text-left text-sm hover:bg-gray-50 flex items-center gap-3 transition-colors"
                                    >
                                      {campaign.status === "ACTIVE" ? (
                                        <>
                                          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                          </svg>
                                          Pause
                                        </>
                                      ) : (
                                        <>
                                          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                          </svg>
                                          Resume
                                        </>
                                      )}
                                    </button>
                                    <div className="border-t border-gray-100"></div>
                                    <button
                                      onClick={() => {
                                        handleDeleteCampaign(campaign);
                                        setOpenSettingsMenu(null);
                                      }}
                                      className="w-full px-4 py-3 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3 transition-colors"
                                    >
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                      </svg>
                                      Delete
                                    </button>
                                  </div>
                                </>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Business Description - Full width on its own row */}
                        <h3 className="text-gray-900 font-medium text-sm sm:text-base mb-2 line-clamp-2">
                          {campaign.business_description}
                        </h3>

                        {/* Stats Row */}
                        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs">
                          <div className="flex items-center gap-1.5 text-gray-600 bg-gray-50 px-2 py-1 rounded-md">
                            <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            <span className="font-medium">{campaign.subreddits_count}</span>
                            <span className="text-gray-400">subreddits</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-gray-600 bg-gray-50 px-2 py-1 rounded-md">
                            <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            <span className="font-medium">{campaign.leads_count}</span>
                            <span className="text-gray-400">leads</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* How It Works Section */}
            <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              {/* Section Header */}
              <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider text-center">How It Works</h3>
              </div>

              {/* Steps Grid */}
              <div className="p-4 sm:p-5">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Step 1 */}
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-lg p-4 border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-gray-900 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <span className="inline-block px-1.5 py-0.5 bg-gray-900 text-white text-[10px] font-semibold rounded-full mb-1.5">1</span>
                        <h4 className="text-sm font-semibold text-gray-900 mb-1">Discover Communities</h4>
                        <p className="text-xs text-gray-500 leading-relaxed">
                          Describe your business and our AI finds relevant subreddits where your potential customers are active.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-lg p-4 border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-gray-900 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <span className="inline-block px-1.5 py-0.5 bg-gray-900 text-white text-[10px] font-semibold rounded-full mb-1.5">2</span>
                        <h4 className="text-sm font-semibold text-gray-900 mb-1">Track Posts</h4>
                        <p className="text-xs text-gray-500 leading-relaxed">
                          We monitor discussions and identify high-intent posts from people looking for solutions like yours.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-lg p-4 border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-gray-900 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <span className="inline-block px-1.5 py-0.5 bg-gray-900 text-white text-[10px] font-semibold rounded-full mb-1.5">3</span>
                        <h4 className="text-sm font-semibold text-gray-900 mb-1">Engage & Convert</h4>
                        <p className="text-xs text-gray-500 leading-relaxed">
                          Review AI-generated responses and engage with potential customers at the perfect moment.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step: Create Radar */}
        {step === "create" && (
          <div className="max-w-2xl mx-auto">
            <button
              onClick={() => setStep("campaigns")}
              className="flex items-center gap-2 text-gray-600 mb-6 hover:text-gray-900 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
              </svg>
              Back to Radars
            </button>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              {/* Header */}
              <div className="px-8 py-6 border-b border-gray-100 bg-gray-50/50">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Create New Radar</h2>
                  <p className="text-sm text-gray-500">Set up automated lead discovery</p>
                </div>
              </div>

              {/* Form Content */}
              <div className="p-8">
                {/* URL Analysis */}
                <div className="mb-8 bg-[#FFF4EE] border border-[#FF4500]/20 rounded-xl p-5">
                  <label className="block text-sm font-semibold text-gray-800 mb-3">
                    Quick Start — Analyze Your Website
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={websiteUrl}
                      onChange={(e) => setWebsiteUrl(e.target.value)}
                      className="flex-1 px-4 py-2.5 border border-[#FF4500]/20 bg-white rounded-xl focus:ring-2 focus:ring-[#FF4500] focus:border-transparent transition-shadow"
                      placeholder="https://yourwebsite.com"
                    />
                    <button
                      onClick={async () => {
                        if (!websiteUrl.trim()) return;
                        setAnalyzingUrl(true);
                        setError("");
                        try {
                          const result = await analyzeUrl(websiteUrl.trim());
                          setBusinessDescription(result.description);
                        } catch (err: unknown) {
                          const message = err instanceof Error ? err.message : "Failed to analyze URL";
                          setError(message);
                        } finally {
                          setAnalyzingUrl(false);
                        }
                      }}
                      disabled={analyzingUrl || !websiteUrl.trim()}
                      className="px-5 py-2.5 bg-[#FF4500] text-white rounded-xl hover:bg-[#e03d00] disabled:opacity-50 transition-colors font-medium text-sm whitespace-nowrap flex items-center gap-2"
                    >
                      {analyzingUrl ? (
                        <>
                          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Analyzing...
                        </>
                      ) : (
                        "Analyze"
                      )}
                    </button>
                  </div>
                  <p className="text-sm text-[#FF4500]/60 mt-2">
                    Paste your website URL to auto-generate a business description
                  </p>
                </div>

                {/* Divider */}
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex-1 border-t border-gray-200" />
                  <span className="text-xs text-gray-400 uppercase tracking-wide font-medium">or describe manually</span>
                  <div className="flex-1 border-t border-gray-100" />
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Describe Your Business
                  </label>
                  <textarea
                    value={businessDescription}
                    onChange={(e) => setBusinessDescription(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-shadow resize-none"
                    rows={5}
                    placeholder="e.g., I sell project management SaaS for small teams"
                  />
                  <p className="text-sm text-gray-400 mt-3">
                    Be specific about your product, target audience, and problems you solve
                  </p>
                </div>

                <button
                  onClick={handleCreateCampaign}
                  disabled={loading}
                  className="w-full px-6 py-3.5 bg-gray-900 text-white rounded-xl hover:bg-gray-800 disabled:opacity-50 transition-colors font-medium text-base"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Creating Radar...
                    </span>
                  ) : (
                    "Create Radar & Discover Subreddits"
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Discover & Select Subreddits */}
        {step === "discover" && (
          <div className="bg-white p-8 rounded-lg border">
            <h2 className="text-2xl font-semibold mb-6">
              Select Subreddits to Monitor
            </h2>

            {loading ? (
              <DiscoveryLoadingState />
            ) : (
              <>
                <div className="mb-6 flex items-center justify-between">
                  <p className="text-gray-600">
                    Selected: {selectedSubreddits.size} / {MAX_SUBREDDIT_SELECTION} subreddits
                    {selectedSubreddits.size >= MAX_SUBREDDIT_SELECTION && (
                      <span className="text-amber-600 ml-2">
                        (max reached)
                        <button
                          onClick={() => {
                            const tier = currentUser?.subscription_tier || "FREE_TRIAL";
                            let recommendedTier = "GROWTH";
                            if (tier.includes("GROWTH")) {
                              recommendedTier = "PRO";
                            } else if (tier.includes("PRO")) {
                              recommendedTier = "PRO";
                            }
                            setUpgradeContext({
                              reason: "subreddit_limit",
                              currentCount: selectedSubreddits.size,
                              maxCount: MAX_SUBREDDIT_SELECTION,
                              recommendedTier,
                            });
                            setShowBillingDialog(true);
                          }}
                          className="text-orange-600 hover:text-orange-700 underline ml-1"
                        >
                          Upgrade for more
                        </button>
                      </span>
                    )}
                  </p>
                </div>

                {(() => {
                  // Sort subreddits: by score descending, then by subscribers descending
                  const sortedSubs = [...subreddits].sort((a, b) => {
                    const scoreA = typeof a.relevance_score === 'number' && a.relevance_score <= 1 ? a.relevance_score : 0;
                    const scoreB = typeof b.relevance_score === 'number' && b.relevance_score <= 1 ? b.relevance_score : 0;
                    if (scoreB !== scoreA) return scoreB - scoreA;
                    return b.subscribers - a.subscribers;
                  });

                  // Split into high score (>=70%) and low score (<70%)
                  const highScoreSubs = sortedSubs.filter(sub =>
                    typeof sub.relevance_score === 'number' && sub.relevance_score <= 1 && sub.relevance_score >= 0.7
                  );
                  const lowScoreSubs = sortedSubs.filter(sub =>
                    typeof sub.relevance_score !== 'number' || sub.relevance_score > 1 || sub.relevance_score < 0.7
                  );

                  // Split high score into visible (first 20) and collapsed
                  const visibleHighScore = highScoreSubs.slice(0, 20);
                  const collapsedHighScore = highScoreSubs.slice(20);

                  const renderSubreddit = (sub: SubredditInfo) => {
                    const isAtLimit = selectedSubreddits.size >= MAX_SUBREDDIT_SELECTION && !selectedSubreddits.has(sub.name);
                    return (
                      <label
                        key={sub.name}
                        className={`flex items-start p-4 border rounded-lg transition ${
                          isAtLimit
                            ? "opacity-50 cursor-not-allowed"
                            : selectedSubreddits.has(sub.name)
                              ? "border-gray-900 bg-gray-100 cursor-pointer"
                              : "hover:bg-gray-50 cursor-pointer"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedSubreddits.has(sub.name)}
                          onChange={() => toggleSubreddit(sub)}
                          disabled={isAtLimit}
                          className="mt-1 mr-3"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium">r/{sub.name}</span>
                            <span className="text-sm text-gray-500">
                              {sub.subscribers.toLocaleString()} subscribers
                            </span>
                            {typeof sub.relevance_score === 'number' && sub.relevance_score <= 1 && (
                              <span className={`text-xs px-2 py-0.5 rounded-full ${
                                sub.relevance_score >= 0.8
                                  ? "bg-green-100 text-green-700"
                                  : sub.relevance_score >= 0.7
                                    ? "bg-yellow-100 text-yellow-700"
                                    : "bg-gray-100 text-gray-600"
                              }`}>
                                {Math.round(sub.relevance_score * 100)}% match
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{sub.description}</p>
                        </div>
                      </label>
                    );
                  };

                  return (
                    <div className="space-y-4 mb-6">
                      {/* High score subreddits (>=70%) - first 20 always visible */}
                      {visibleHighScore.length > 0 && (
                        <div className="grid gap-3">
                          {visibleHighScore.map(renderSubreddit)}
                        </div>
                      )}

                      {/* Collapsed high score subreddits (>20 with >=70%) */}
                      {collapsedHighScore.length > 0 && (
                        <div>
                          <button
                            onClick={() => setShowMoreHighScore(!showMoreHighScore)}
                            className="w-full py-2 px-4 text-sm text-gray-600 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center justify-center gap-2"
                          >
                            <svg
                              className={`w-4 h-4 transition-transform ${showMoreHighScore ? 'rotate-180' : ''}`}
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                            </svg>
                            {showMoreHighScore ? 'Hide' : 'Show'} {collapsedHighScore.length} more recommended subreddits
                          </button>
                          {showMoreHighScore && (
                            <div className="grid gap-3 mt-3">
                              {collapsedHighScore.map(renderSubreddit)}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Low score subreddits (<70%) - collapsed by default */}
                      {lowScoreSubs.length > 0 && (
                        <div>
                          <button
                            onClick={() => setShowLowScore(!showLowScore)}
                            className="w-full py-2 px-4 text-sm text-gray-500 bg-gray-50 rounded-lg hover:bg-gray-100 flex items-center justify-center gap-2"
                          >
                            <svg
                              className={`w-4 h-4 transition-transform ${showLowScore ? 'rotate-180' : ''}`}
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                            </svg>
                            {showLowScore ? 'Hide' : 'Show'} {lowScoreSubs.length} less relevant subreddits (&lt;70% match)
                          </button>
                          {showLowScore && (
                            <div className="grid gap-3 mt-3">
                              {lowScoreSubs.map(renderSubreddit)}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })()}

                <div className="flex gap-3">
                  <button
                      onClick={() => {
                      setStep("campaigns");
                      setSelectedSubreddits(new Map());
                    }}
                    className="px-6 py-3 border rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSelectSubreddits}
                    disabled={selectedSubreddits.size === 0}
                    className="flex-1 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
                  >
                    Activate Radar ({selectedSubreddits.size} subreddits)
                  </button>
                </div>
              </>
            )}
          </div>
        )}
            </div>
          </div>
        )}

        {/* Step: View Leads - Inbox Style */}
        {step === "leads" && currentCampaign && (
          <div className="fixed inset-0 bg-white flex">
            {/* Left Sidebar - Subreddit Filters (hidden below xl breakpoint) */}
            <div className="hidden xl:flex w-64 border-r bg-gray-50 flex-col flex-shrink-0">
              {/* Scrollable content area */}
              <div className="flex-1 overflow-y-auto pt-8 px-6 pb-6">
                <button
                  onClick={() => {
                    setStep("campaigns");
                    setLeads([]);
                    setSelectedLead(null);
                  }}
                  className="text-gray-600 mb-6 hover:text-gray-900 text-xs flex items-center gap-1"
                >
                  <span>←</span> Back to Radars
                </button>

                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-semibold">Inbox</h2>
                    {/* Scanning indicator */}
                    {isStreaming && (
                      <div className="flex items-center gap-1.5 px-2 py-1 bg-green-50 text-green-700 rounded-full border border-green-200 animate-pulse">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-ping" />
                        <span className="text-xs font-medium">Scanning...</span>
                      </div>
                    )}
                  </div>
                  {/* Overall Relevancy Badge */}
                  {!isStreaming && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-50 text-green-700 rounded-lg border border-green-200">
                      <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                      <span className="text-xs font-semibold">
                        {leads.length > 0 ? Math.round(leads.reduce((acc, l) => {
                          const score = l.relevancy_score || 0;
                          return acc + (score <= 1 ? score * 100 : score);
                        }, 0) / leads.length) : 0}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Status Tabs */}
                <div className="mb-4">
                  <div className="space-y-0.5">
                    {["Inbox", "Contacted"].map((tab, idx) => {
                      const statusMap: Record<string, string> = {
                        "Inbox": "NEW",
                        "Contacted": "CONTACTED"
                      };
                      const countMap: Record<string, number> = {
                        "Inbox": leadCounts.new,
                        "Contacted": leadCounts.contacted
                      };
                      const status = statusMap[tab];
                      const count = countMap[tab];

                      return (
                        <button
                          key={tab}
                          onClick={async () => {
                            // 立即更新filterStatus并重新加载数据
                            setFilterStatus(status);
                            await handleViewLeads(currentCampaign, status);
                          }}
                          className={`w-full text-left px-2.5 py-1.5 rounded text-xs flex justify-between items-center ${
                            filterStatus === status
                              ? "bg-gray-200 font-medium"
                              : "hover:bg-gray-100"
                          }`}
                        >
                          <span>{tab}</span>
                          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                            filterStatus === status
                              ? "bg-gray-900 text-white"
                              : "bg-gray-200 text-gray-600"
                          }`}>
                            {count}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Subreddit Filter */}
                <div>
                  <div className="flex items-center justify-between mb-1.5 px-2.5">
                    <h3 className="text-[10px] font-semibold text-gray-500 uppercase">
                      Filter by Subreddit
                    </h3>
                    <button
                      onClick={handleOpenAddSubreddit}
                      className="text-gray-900 hover:text-gray-700"
                      title="Add Subreddit"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                      </svg>
                    </button>
                  </div>
                  <button
                    onClick={() => setSelectedSubreddit("all")}
                    className={`w-full text-left px-2.5 py-1.5 rounded text-xs flex justify-between items-center ${
                      selectedSubreddit === "all"
                        ? "bg-gray-200 font-medium"
                        : "hover:bg-gray-100"
                    }`}
                  >
                    <span>All subreddits</span>
                    <span className="text-[10px] text-gray-500">{leads.length}</span>
                  </button>

                  {Array.from(new Set(leads.map(l => l.subreddit_name))).map((subreddit) => {
                    const count = leads.filter(l => l.subreddit_name === subreddit).length;
                    return (
                      <button
                        key={subreddit}
                        onClick={() => setSelectedSubreddit(subreddit)}
                        className={`w-full text-left px-2.5 py-1.5 rounded text-xs flex justify-between items-center ${
                          selectedSubreddit === subreddit
                            ? "bg-gray-200 font-medium"
                            : "hover:bg-gray-100"
                        }`}
                      >
                        <span>r/{subreddit}</span>
                        <span className="text-[10px] text-gray-500">{count}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Subscription Status Card */}
              {currentUser && (
                <SubscriptionStatusCard
                  user={currentUser}
                  onSubscribe={() => setShowBillingDialog(true)}
                />
              )}

              {/* User Profile Section */}
              {currentUser && (
                <div className="border-t border-gray-200 px-3 py-3">
                  <UserMenu
                    user={currentUser}
                    position="top"
                    compact
                    onBilling={() => setShowBillingDialog(true)}
                  />
                </div>
              )}
            </div>

            {/* Center - Leads List */}
            <div className="flex-1 flex flex-col overflow-hidden min-w-0">
              {/* Mobile Header with Back (below lg) */}
              <div className="lg:hidden border-b px-4 py-3 flex items-center gap-3 bg-white">
                <button
                  onClick={() => {
                    setStep("campaigns");
                    setLeads([]);
                    setSelectedLead(null);
                  }}
                  className="p-1.5 -ml-1.5 text-gray-600 hover:text-gray-900"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <h2 className="text-lg font-bold flex-1">Inbox</h2>
                {!isStreaming && (
                  <div className="flex items-center gap-1.5 px-2 py-1 bg-green-50 text-green-700 rounded-lg border border-green-200">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                    <span className="text-xs font-semibold">
                      {leads.length > 0 ? Math.round(leads.reduce((acc, l) => {
                        const score = l.relevancy_score || 0;
                        return acc + (score <= 1 ? score * 100 : score);
                      }, 0) / leads.length) : 0}%
                    </span>
                  </div>
                )}
              </div>
              {/* Desktop Header (lg and above) */}
              <div className="hidden lg:flex border-b px-6 pt-3 pb-3 items-center justify-between bg-white">
                {/* Back button - shown only between lg and xl when sidebar is hidden */}
                <button
                  onClick={() => {
                    setStep("campaigns");
                    setLeads([]);
                    setSelectedLead(null);
                  }}
                  className="xl:hidden mr-4 text-gray-600 hover:text-gray-900 text-xs flex items-center gap-1"
                >
                  <span>←</span> Back
                </button>
                <div className="flex items-center gap-4">
                  {/* Sort Dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => {
                        const sortButton = document.getElementById('sort-select');
                        sortButton?.focus();
                      }}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer"
                    >
                      <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                      </svg>
                      <span className="text-gray-700">
                        {sortOrder === "relevancy" ? "Sort by Relevancy" : "Sort by Time"}
                      </span>
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    <select
                      id="sort-select"
                      value={sortOrder}
                      onChange={(e) => setSortOrder(e.target.value as "relevancy" | "time")}
                      className="absolute inset-0 w-full opacity-0 cursor-pointer"
                    >
                      <option value="relevancy">Sort by Relevancy</option>
                      <option value="time">Sort by Time</option>
                    </select>
                  </div>

                  {/* Run Now Button - hidden in production via env var */}
                  {currentUser?.id === 1 && currentCampaign && currentCampaign.status === "ACTIVE" && (
                    <button
                      onClick={() => handleRunNow(currentCampaign)}
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      {loading ? "Running..." : "Fetch Leads"}
                    </button>
                  )}
                </div>
              </div>

              {/* Leads List */}
              <div className="flex-1 overflow-y-auto mt-1">
                {loading ? (
                  <div className="text-center py-16">
                    <div className="max-w-sm mx-auto">
                      {/* Animated icon */}
                      <div className="flex justify-center mb-6">
                        <div className="relative">
                          <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                            <svg className="w-7 h-7 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                          </div>
                          <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full flex items-center justify-center shadow">
                            <svg className="w-3 h-3 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                          </div>
                        </div>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Fetching leads...</h3>
                      <p className="text-sm text-gray-500 mb-4">
                        Scanning subreddits and analyzing posts. This may take a few minutes.
                      </p>
                      <p className="text-xs text-gray-400">
                        Feel free to leave and come back later - we&apos;ll keep working in the background.
                      </p>
                    </div>
                  </div>
                ) : leads.filter(l => selectedSubreddit === "all" || l.subreddit_name === selectedSubreddit).length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-500">No leads found</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Try changing filters or wait for the next polling cycle
                    </p>
                    {currentUser?.id === 1 && currentCampaign && currentCampaign.status === "ACTIVE" && (
                      <button
                        onClick={() => handleRunNow(currentCampaign)}
                        disabled={loading}
                        className="mt-4 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        {loading ? "Fetching..." : "Fetch Leads Now"}
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="p-3 space-y-2">
                    {leads
                      .filter(l => selectedSubreddit === "all" || l.subreddit_name === selectedSubreddit)
                      .sort((a, b) => {
                        if (sortOrder === "relevancy") {
                          // Primary: Sort by relevancy score descending
                          const scoreA = a.relevancy_score || 0;
                          const scoreB = b.relevancy_score || 0;
                          if (scoreB !== scoreA) {
                            return scoreB - scoreA;
                          }
                          // Secondary: Same relevancy, sort by time descending (newest first)
                          return (b.created_utc || 0) - (a.created_utc || 0);
                        } else {
                          // Primary: Sort by time descending (newest first)
                          const timeA = a.created_utc || 0;
                          const timeB = b.created_utc || 0;
                          if (timeB !== timeA) {
                            return timeB - timeA;
                          }
                          // Secondary: Same time, sort by relevancy descending
                          const scoreA = a.relevancy_score || 0;
                          const scoreB = b.relevancy_score || 0;
                          return scoreB - scoreA;
                        }
                      })
                      .map((lead) => {
                        const timeAgo = getTimeAgo(lead.created_utc || 0);
                        const score = lead.relevancy_score || 0;
                        // Support both old (0.0-1.0) and new (0-100) formats
                        const relevancyPercent = Math.round(score <= 1 ? score * 100 : score);
                        // Get score tier label and color
                        const getScoreTier = (score: number) => {
                          if (score >= 90) return { label: "HOT", color: "text-red-600", bg: "bg-red-50", border: "border-red-200" };
                          if (score >= 80) return { label: "HIGH", color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200" };
                          if (score >= 70) return { label: "GOOD", color: "text-yellow-600", bg: "bg-yellow-50", border: "border-yellow-200" };
                          if (score >= 60) return { label: "MED", color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200" };
                          return { label: "LOW", color: "text-gray-500", bg: "bg-gray-50", border: "border-gray-200" };
                        };
                        const tier = getScoreTier(relevancyPercent);
                        // Format timestamp for display
                        const formatTimestamp = () => {
                          if (!lead.created_utc) return '';
                          const date = new Date(lead.created_utc * 1000);
                          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) + ' | ' + date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
                        };
                        return (
                          <div
                            key={lead.id}
                            onClick={() => handleSelectLead(lead)}
                            className={`bg-white rounded-lg border cursor-pointer transition-all hover:shadow-sm ${
                              selectedLead?.id === lead.id
                                ? "ring-1 ring-gray-900 border-gray-900"
                                : "border-gray-200 hover:border-gray-300"
                            }`}
                          >
                            <div className="flex items-stretch">
                              {/* Left: Score Section */}
                              <div className={`flex flex-col items-center justify-center px-3 py-3 ${tier.bg} rounded-l-lg border-r ${tier.border} min-w-[56px]`}>
                                <span className={`text-xl font-bold ${tier.color}`}>{relevancyPercent}</span>
                                <span className={`text-[9px] font-semibold ${tier.color} tracking-wide`}>{tier.label}</span>
                              </div>

                              {/* Middle: Content */}
                              <div className="flex-1 p-3 min-w-0">
                                {/* Header: Reddit icon, subreddit, timestamp */}
                                <div className="flex items-center gap-1.5 mb-1.5">
                                  <svg className="w-4 h-4 text-orange-500 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
                                  </svg>
                                  <span className="font-medium text-xs text-gray-900">r/{lead.subreddit_name || 'unknown'}</span>
                                  <span className="text-[11px] text-gray-400">{formatTimestamp()}</span>
                                </div>

                                {/* Title */}
                                <h3 className="font-semibold text-[13px] text-gray-900 mb-1 line-clamp-1">
                                  {lead.title || 'Untitled'}
                                </h3>

                                {/* Content preview */}
                                <p className="text-xs text-gray-500 line-clamp-2 mb-2">
                                  {lead.content ? (lead.content.substring(0, 180) + (lead.content.length > 180 ? '...' : '')) : 'No content'}
                                </p>

                                {/* Bottom: Stats */}
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="inline-flex items-center gap-0.5 text-[11px] text-gray-400">
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                                    </svg>
                                    {lead.score || 0}
                                  </span>
                                  <span className="inline-flex items-center gap-0.5 text-[11px] text-gray-400">
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                    </svg>
                                    {lead.num_comments || 0}
                                  </span>
                                  {lead.author && (
                                    <span className="text-[11px] text-gray-400">by u/{lead.author}</span>
                                  )}
                                </div>
                              </div>

                              {/* Right: Action Icons */}
                              <div className="flex flex-col items-center justify-center gap-1.5 px-2 border-l border-gray-100">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleUpdateStatus(lead.id, lead.status === "CONTACTED" ? "NEW" : "CONTACTED");
                                  }}
                                  className={`p-1 rounded-md transition-colors ${
                                    lead.status === "CONTACTED"
                                      ? "text-green-600 bg-green-50 hover:bg-green-100"
                                      : "text-gray-400 hover:text-green-600 hover:bg-green-50"
                                  }`}
                                  title={lead.status === "CONTACTED" ? "Move to inbox" : "Mark as contacted"}
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                  </svg>
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleUpdateStatus(lead.id, "DISMISSED");
                                  }}
                                  className={`p-1 rounded-md transition-colors ${
                                    lead.status === "DISMISSED"
                                      ? "text-red-600 bg-red-50 hover:bg-red-100"
                                      : "text-gray-400 hover:text-red-600 hover:bg-red-50"
                                  }`}
                                  title="Dismiss"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            </div>

            {/* Right Panel - Lead Details (bottom drawer on mobile, responsive on tablet/desktop) */}
            {selectedLead && (
              <>
                {/* Mobile backdrop */}
                <div
                  className="lg:hidden fixed inset-0 bg-black/40 z-40"
                  onClick={() => setSelectedLead(null)}
                />
                <div
                  className="fixed inset-x-0 bottom-0 top-16 lg:top-0 lg:relative lg:inset-auto lg:border-l bg-white overflow-y-auto z-50 lg:z-auto lg:w-1/2 xl:w-auto flex-shrink-0 rounded-t-2xl lg:rounded-none shadow-[0_-4px_20px_rgba(0,0,0,0.15)] lg:shadow-none"
                  style={isXlScreen ? { width: `${detailPanelWidth}px` } : undefined}
                >
                {/* Mobile Drawer Header with drag handle and close button */}
                <div className="lg:hidden sticky top-0 bg-white z-10 px-3 pt-2 rounded-t-2xl">
                  {/* Drag handle and close in one row */}
                  <div className="flex items-center justify-between">
                    <div className="w-5"></div>
                    <div className="w-10 h-1 bg-gray-300 rounded-full"></div>
                    <button
                      onClick={() => setSelectedLead(null)}
                      className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
                {/* Resize Handle (only shown on xl+ when custom width is applied) */}
                <div
                  className={`hidden xl:block absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-900 transition-colors ${
                    isResizing ? 'bg-gray-900' : 'bg-transparent'
                  }`}
                  onMouseDown={handleMouseDown}
                  style={{ zIndex: 10 }}
                >
                  <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 rounded-full" />
                </div>
                <div className="p-5 space-y-3 bg-gray-50">
                  {/* Combined Header + Content Card */}
                  {(() => {
                    const score = selectedLead.relevancy_score || 0;
                    const relevancyPercent = Math.round(score <= 1 ? score * 100 : score);
                    const getScoreTier = (s: number) => {
                      if (s >= 90) return { label: "HOT", color: "text-red-600", bg: "bg-red-50", border: "border-red-200" };
                      if (s >= 80) return { label: "HIGH", color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200" };
                      if (s >= 70) return { label: "GOOD", color: "text-yellow-600", bg: "bg-yellow-50", border: "border-yellow-200" };
                      if (s >= 60) return { label: "MED", color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200" };
                      return { label: "LOW", color: "text-gray-500", bg: "bg-gray-50", border: "border-gray-200" };
                    };
                    const tier = getScoreTier(relevancyPercent);
                    const formatTimestamp = () => {
                      if (!selectedLead.created_utc) return '';
                      const date = new Date(selectedLead.created_utc * 1000);
                      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) + ' | ' + date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
                    };
                    return (
                      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                        {/* Header: Score + Meta */}
                        <div className="flex items-center gap-3 p-3 border-b border-gray-100">
                          {/* Score Circle */}
                          <div className={`w-12 h-12 rounded-full ${tier.bg} border-2 ${tier.border} flex flex-col items-center justify-center flex-shrink-0`}>
                            <span className={`text-base font-bold ${tier.color} leading-none`}>{relevancyPercent}</span>
                            <span className={`text-[8px] font-semibold ${tier.color} tracking-wide`}>{tier.label}</span>
                          </div>
                          {/* Meta Info */}
                          <div className="flex-1">
                            <div className="flex items-center gap-1.5 mb-1.5">
                              <svg className="w-4 h-4 text-orange-500 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
                              </svg>
                              <span className="font-medium text-xs text-gray-900">r/{selectedLead.subreddit_name || 'unknown'}</span>
                              <span className="text-[11px] text-gray-400">{formatTimestamp()}</span>
                            </div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                u/{selectedLead.author || '[deleted]'}
                              </span>
                              <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                                </svg>
                                {selectedLead.score || 0}
                              </span>
                              <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                                {selectedLead.num_comments || 0}
                              </span>
                              {selectedLead.post_url && (
                                <a
                                  href={selectedLead.post_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-[11px] text-orange-500 hover:text-orange-600 transition-colors"
                                  title="View on Reddit"
                                >
                                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                  </svg>
                                  Open
                                </a>
                              )}
                            </div>
                          </div>
                        </div>
                        {/* Post Content */}
                        <div className="p-4">
                          <h2 className="text-sm font-semibold text-gray-900 mb-2">
                            {selectedLead.title || 'Untitled'}
                          </h2>
                          <p className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
                            {selectedLead.content || 'No content available'}
                          </p>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Reasoning Card */}
                  <div className="bg-white rounded-xl border border-green-200 shadow-sm overflow-hidden">
                    <div className="px-3 py-2 bg-green-50 border-b border-green-200 flex items-center gap-1.5">
                      <svg className="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <span className="text-xs font-semibold text-green-800">Why this is a lead</span>
                    </div>
                    <div className="p-3">
                      <p className="text-xs text-gray-700 leading-relaxed">
                        {selectedLead.relevancy_reason || 'No reasoning available'}
                      </p>
                    </div>
                  </div>

                  {/* Suggested Comment Card */}
                  <div className="bg-white rounded-xl border border-amber-200 shadow-sm overflow-hidden">
                    <div className="px-3 py-2 bg-amber-50 border-b border-amber-200 flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <svg className="w-3.5 h-3.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                        </svg>
                        <span className="text-xs font-semibold text-amber-800">Suggested Comment</span>
                      </div>
                      {loadingSuggestions && (
                        <span className="text-[10px] text-amber-600 flex items-center gap-1">
                          <svg className="w-2.5 h-2.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Generating...
                        </span>
                      )}
                    </div>
                    <div className="p-3">
                      {loadingSuggestions ? (
                        <div className="animate-pulse">
                          <div className="h-3 bg-amber-100 rounded w-3/4 mb-2" />
                          <div className="h-3 bg-amber-100 rounded w-1/2" />
                        </div>
                      ) : (
                        <p className="text-xs text-gray-700 leading-relaxed mb-3">
                          {selectedLead.suggested_comment || 'No suggested comment available'}
                        </p>
                      )}
                      <button
                        onClick={() => handleCopyAndComment(selectedLead)}
                        disabled={loadingSuggestions || !selectedLead.suggested_comment}
                        className="w-full px-3 py-2 bg-gray-900 text-white rounded-lg text-xs font-medium hover:bg-gray-800 flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Copy & Comment
                      </button>
                    </div>
                  </div>

                  {/* Suggested DM Card */}
                  <div className="bg-white rounded-xl border border-amber-200 shadow-sm overflow-hidden">
                    <div className="px-3 py-2 bg-amber-50 border-b border-amber-200 flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <svg className="w-3.5 h-3.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span className="text-xs font-semibold text-amber-800">Suggested DM</span>
                      </div>
                      {loadingSuggestions && (
                        <span className="text-[10px] text-amber-600 flex items-center gap-1">
                          <svg className="w-2.5 h-2.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Generating...
                        </span>
                      )}
                    </div>
                    <div className="p-3">
                      {loadingSuggestions ? (
                        <div className="animate-pulse">
                          <div className="h-3 bg-amber-100 rounded w-3/4 mb-2" />
                          <div className="h-3 bg-amber-100 rounded w-2/3 mb-2" />
                          <div className="h-3 bg-amber-100 rounded w-1/2" />
                        </div>
                      ) : (
                        <p className="text-xs text-gray-700 leading-relaxed mb-3">
                          {selectedLead.suggested_dm || 'No suggested DM available'}
                        </p>
                      )}
                      <button
                        onClick={() => handleCopyAndDM(selectedLead)}
                        disabled={loadingSuggestions || !selectedLead.suggested_dm}
                        className="w-full px-3 py-2 bg-gray-900 text-white rounded-lg text-xs font-medium hover:bg-gray-800 flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Copy & DM
                      </button>
                    </div>
                  </div>

                </div>
              </div>
              </>
            )}
          </div>
        )}

        {/* Add Subreddit Modal */}
        {showAddSubredditModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full mx-4 max-h-[80vh] flex flex-col">
              {/* Modal Header */}
              <div className="px-6 py-4 border-b flex items-center justify-between">
                <h2 className="text-xl font-bold">Add Subreddits</h2>
                <button
                  onClick={() => {
                    setShowAddSubredditModal(false);
                    setSelectedNewSubreddits(new Set());
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Body */}
              <div className="flex-1 overflow-hidden flex">
                {/* Left Side - Tracked Subreddits */}
                <div className="w-1/2 border-r overflow-y-auto">
                  <div className="p-6">
                    <h3 className="text-lg font-semibold mb-4">Currently Tracking ({trackedSubreddits.length})</h3>
                    {loadingTracked ? (
                      <div className="text-center py-8">
                        <div className="inline-flex items-center gap-2 text-gray-500">
                          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          <span>Loading tracked subreddits...</span>
                        </div>
                      </div>
                    ) : trackedSubreddits.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        No subreddits tracked yet
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {trackedSubreddits.map((sub) => (
                          <div
                            key={sub.name}
                            className="p-4 border rounded-lg bg-gray-50"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                              </svg>
                              <span className="font-medium">r/{sub.name}</span>
                              <span className="text-sm text-gray-500">
                                {sub.subscribers.toLocaleString()} members
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 line-clamp-2">
                              {sub.description || sub.title}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Side - Recommended Subreddits */}
                <div className="w-1/2 overflow-y-auto">
                  <div className="p-6">
                    <h3 className="text-lg font-semibold mb-4">
                      Recommended for Your Business ({recommendedSubreddits.length})
                    </h3>
                    {loadingRecommended ? (
                      <div className="text-center py-8">
                        <div className="inline-flex items-center gap-2 text-gray-500">
                          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          <span>Finding recommendations...</span>
                        </div>
                      </div>
                    ) : recommendedSubreddits.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        No new recommendations found
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {recommendedSubreddits.map((sub) => (
                          <label
                            key={sub.name}
                            className={`block p-4 border rounded-lg cursor-pointer transition ${
                              selectedNewSubreddits.has(sub.name)
                                ? "border-gray-900 bg-gray-100"
                                : "hover:bg-gray-50"
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <input
                                type="checkbox"
                                checked={selectedNewSubreddits.has(sub.name)}
                                onChange={() => toggleNewSubreddit(sub.name)}
                                className="mt-1"
                              />
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium">r/{sub.name}</span>
                                  <span className="text-sm text-gray-500">
                                    {sub.subscribers.toLocaleString()} members
                                  </span>
                                  {sub.relevance_score != null && sub.relevance_score <= 1 && (
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                                      sub.relevance_score >= 0.8
                                        ? "bg-green-100 text-green-700"
                                        : sub.relevance_score >= 0.5
                                          ? "bg-yellow-100 text-yellow-700"
                                          : "bg-gray-100 text-gray-600"
                                    }`}>
                                      {Math.round(sub.relevance_score * 100)}% match
                                    </span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 line-clamp-2">
                                  {sub.description || sub.title}
                                </p>
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 border-t flex items-center justify-between bg-gray-50">
                <div className="text-sm text-gray-600">
                  {selectedNewSubreddits.size > 0 && (
                    <span>{selectedNewSubreddits.size} subreddit(s) selected</span>
                  )}
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowAddSubredditModal(false);
                      setSelectedNewSubreddits(new Set());
                    }}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-100"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddSelectedSubreddits}
                    disabled={selectedNewSubreddits.size === 0 || loading}
                    className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? "Adding..." : `Add ${selectedNewSubreddits.size} Subreddit(s)`}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      {/* Streaming Progress Modal */}
      {isStreaming && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full mx-4 p-6">
            {/* Simple Progress */}
            <div className="text-center">
              {/* Animated icon */}
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-orange-500 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {streamProgress?.phase === "fetching" && "Scanning subreddits..."}
                {streamProgress?.phase === "scoring" && "Analyzing posts..."}
                {streamProgress?.phase === "suggestions" && "Almost done..."}
                {!streamProgress && "Starting..."}
              </h3>

              {/* Progress bar */}
              {streamProgress && (
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden mb-4">
                  <div
                    className="h-full bg-orange-500 rounded-full transition-all duration-300"
                    style={{ width: `${Math.round((streamProgress.current / streamProgress.total) * 100)}%` }}
                  />
                </div>
              )}

              {/* Leads counter */}
              {streamingLeads.length > 0 && (
                <p className="text-sm text-gray-600">
                  <span className="font-semibold text-orange-600">{streamingLeads.length}</span> leads found
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Streaming Complete Modal */}
      {streamComplete && !isStreaming && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">{streamComplete.total_leads}</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {streamComplete.total_leads > 0 ? "New Leads Found!" : "Polling Complete"}
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                {streamComplete.total_leads > 0
                  ? `Discovered ${streamComplete.total_leads} leads from ${streamComplete.total_posts_fetched} posts across ${streamComplete.subreddits_polled || 0} subreddits.`
                  : `Scanned ${streamComplete.total_posts_fetched} posts but none were relevant enough.`}
              </p>

              {/* Relevancy distribution */}
              {streamComplete.relevancy_distribution && streamComplete.total_leads > 0 && (
                <div className="bg-gray-50 rounded-lg p-3 mb-4 text-left">
                  <p className="text-xs font-medium text-gray-500 mb-2">By Relevancy Score</p>
                  <div className="space-y-1">
                    {Object.entries(streamComplete.relevancy_distribution)
                      .filter(([, count]) => count > 0)
                      .map(([tier, count]) => (
                        <div key={tier} className="flex justify-between text-sm">
                          <span className="text-gray-600">{tier}</span>
                          <span className="font-medium text-gray-900">{count}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => setStreamComplete(null)}
                className="w-full px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
              >
                View Leads
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Radar Modal */}
      {showDeleteModal && campaignToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">Delete Radar</h3>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setCampaignToDelete(null);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              <p className="text-sm text-gray-600 mb-4">
                Are you sure you want to delete this radar?
              </p>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm font-medium text-gray-900 line-clamp-2">
                  {campaignToDelete.business_description}
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50 rounded-b-xl">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setCampaignToDelete(null);
                }}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteCampaign}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Dialog */}
      {showSuccessDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
            <div className="p-6 text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 relative">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                {/* Pulsing ring animation */}
                <span className="absolute inset-0 rounded-full bg-green-400 opacity-30 animate-ping" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Radar Activated</h3>
              <p className="text-sm text-gray-600 mb-2">
                Your first scan is starting now!
              </p>
              <p className="text-xs text-gray-500 mb-6">
                Leads will appear as they are discovered.
              </p>
              <button
                onClick={async () => {
                  setShowSuccessDialog(false);
                  setSelectedSubreddits(new Map());
                  // Navigate into the campaign - handleViewLeads will fetch data and set step
                  if (currentCampaign) {
                    await handleViewLeads(currentCampaign);
                  } else {
                    setStep("campaigns");
                  }
                }}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                View Leads
              </button>
            </div>
          </div>
        </div>
      )}
      </DashboardLayout>

      {/* Billing Dialog - also handles upgrade prompts via upgradeContext */}
      <BillingDialog
        isOpen={showBillingDialog}
        onClose={() => {
          setShowBillingDialog(false);
          setUpgradeContext(undefined); // Clear upgrade context on close
        }}
        user={currentUser}
        upgradeContext={upgradeContext}
      />
    </ProtectedRoute>
  );
}

export default function RedditPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    }>
      <RedditPageContent />
    </Suspense>
  );
}
