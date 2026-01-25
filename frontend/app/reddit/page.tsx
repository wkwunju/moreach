"use client";

import { useState, useEffect } from "react";
import {
  createRedditCampaign,
  discoverSubreddits,
  selectSubreddits,
  fetchRedditCampaigns,
  fetchRedditLeads,
  updateLeadStatus,
  pauseCampaign,
  resumeCampaign,
  runCampaignNow,
  fetchCampaignSubreddits,
  deleteCampaign,
} from "@/lib/api";
import type { RedditCampaign, SubredditInfo, RedditLead } from "@/lib/types";
import ProtectedRoute from "@/components/ProtectedRoute";
import Dropdown from "@/components/Dropdown";
import DashboardLayout from "@/components/DashboardLayout";

type Step = "campaigns" | "create" | "discover" | "leads";

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

export default function RedditPage() {
  const [step, setStep] = useState<Step>("campaigns");
  const [campaigns, setCampaigns] = useState<RedditCampaign[]>([]);
  const [currentCampaign, setCurrentCampaign] = useState<RedditCampaign | null>(null);
  const [subreddits, setSubreddits] = useState<SubredditInfo[]>([]);
  const [selectedSubreddits, setSelectedSubreddits] = useState<Map<string, SubredditInfo>>(new Map());
  const [leads, setLeads] = useState<RedditLead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Form states
  const [businessDescription, setBusinessDescription] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("NEW");
  
  // Inbox view states
  const [selectedLead, setSelectedLead] = useState<RedditLead | null>(null);
  const [selectedSubreddit, setSelectedSubreddit] = useState<string>("all");
  
  // Lead counts by status
  const [leadCounts, setLeadCounts] = useState({ new: 0, reviewed: 0, contacted: 0 });
  
  // Sort order state
  const [sortOrder, setSortOrder] = useState<"relevancy" | "time">("relevancy");
  
  // Add Subreddit modal states
  const [showAddSubredditModal, setShowAddSubredditModal] = useState(false);
  const [trackedSubreddits, setTrackedSubreddits] = useState<SubredditInfo[]>([]);
  const [recommendedSubreddits, setRecommendedSubreddits] = useState<SubredditInfo[]>([]);
  const [loadingSubreddits, setLoadingSubreddits] = useState(false);
  const [selectedNewSubreddits, setSelectedNewSubreddits] = useState<Set<string>>(new Set());
  
  // Delete campaign modal states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [campaignToDelete, setCampaignToDelete] = useState<RedditCampaign | null>(null);

  // Success dialog state
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);

  // Subreddit display states
  const [showMoreHighScore, setShowMoreHighScore] = useState(false);
  const [showLowScore, setShowLowScore] = useState(false);
  const MAX_SUBREDDIT_SELECTION = 15;

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

  // Load campaigns on mount
  useEffect(() => {
    loadCampaigns();
  }, []);

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
    try {
      setLoading(true);
      setCurrentCampaign(campaign);
      // Use provided status or fall back to filterStatus
      const statusToUse = status !== undefined ? status : filterStatus;
      const data = await fetchRedditLeads(campaign.id, statusToUse);
      setLeads(data.leads);
      setLeadCounts({
        new: data.new_leads,
        reviewed: data.reviewed_leads,
        contacted: data.contacted_leads
      });
      setSelectedLead(data.leads.length > 0 ? data.leads[0] : null);
      setStep("leads");
    } catch (err) {
      setError("Failed to load leads");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdateStatus(leadId: number, status: string) {
    try {
      await updateLeadStatus(leadId, status);
      // Refresh leads
      if (currentCampaign) {
        const data = await fetchRedditLeads(currentCampaign.id, filterStatus);
        setLeads(data.leads);
      }
    } catch (err) {
      setError("Failed to update lead status");
    }
  }

  async function handleCopyAndComment(lead: RedditLead) {
    try {
      // Copy suggested comment to clipboard
      await navigator.clipboard.writeText(lead.suggested_comment || '');
      
      // Update status to "Commented" (REVIEWED)
      await handleUpdateStatus(lead.id, "REVIEWED");
      
      // Open Reddit post in new tab
      window.open(lead.post_url, '_blank');
      
      // 移除当前lead（因为它已经不在当前tab了）
      setLeads(prevLeads => prevLeads.filter(l => l.id !== lead.id));
      // 选择下一个lead
      const nextLead = leads.find(l => l.id !== lead.id);
      setSelectedLead(nextLead || null);
    } catch (err) {
      setError("Failed to copy comment");
    }
  }

  async function handleCopyAndDM(lead: RedditLead) {
    try {
      // Copy suggested DM to clipboard
      await navigator.clipboard.writeText(lead.suggested_dm || '');
      
      // Update status to "DMed" (CONTACTED)
      await handleUpdateStatus(lead.id, "CONTACTED");
      
      // Open Reddit user page in new tab
      const userPageUrl = `https://www.reddit.com/user/${lead.author}`;
      window.open(userPageUrl, '_blank');
      
      // 移除当前lead（因为它已经不在当前tab了）
      setLeads(prevLeads => prevLeads.filter(l => l.id !== lead.id));
      // 选择下一个lead
      const nextLead = leads.find(l => l.id !== lead.id);
      setSelectedLead(nextLead || null);
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
    try {
      setLoading(true);
      setError("");
      const result = await runCampaignNow(campaign.id);
      
      const { summary } = result;
      if (summary.subreddits_polled === 0) {
        alert(`⚠️ No subreddits to poll. Please make sure you've selected subreddits for this radar.`);
      } else if (summary.total_leads_created === 0) {
        alert(`✅ Polling complete!\nChecked ${summary.subreddits_polled} subreddit(s) and found ${summary.total_posts_found} posts, but none were relevant enough (score < 50%).\n\nTry adjusting your business description or selecting different subreddits.`);
      } else {
        alert(`✅ Success!\nFound ${summary.total_leads_created} new leads from ${summary.subreddits_polled} subreddit(s).`);
      }
      
      loadCampaigns();
    } catch (err: any) {
      setError(err.message || "Failed to run radar");
    } finally {
      setLoading(false);
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
        return; // Don't add more if at limit
      }
      newMap.set(subreddit.name, subreddit);
    }
    setSelectedSubreddits(newMap);
  }

  async function handleOpenAddSubreddit() {
    if (!currentCampaign) return;
    
    setShowAddSubredditModal(true);
    setLoadingSubreddits(true);
    
    try {
      // Fetch tracked subreddits
      const tracked = await fetchCampaignSubreddits(currentCampaign.id);
      setTrackedSubreddits(tracked);
      
      // Fetch recommended subreddits
      const recommended = await discoverSubreddits(currentCampaign.id);
      // Filter out already tracked ones
      const trackedNames = new Set(tracked.map(s => s.name));
      const filtered = recommended.filter(s => !trackedNames.has(s.name));
      setRecommendedSubreddits(filtered);
    } catch (err) {
      setError("Failed to load subreddits");
    } finally {
      setLoadingSubreddits(false);
    }
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
      <DashboardLayout>
        <div className="p-8">
          <div className="max-w-7xl mx-auto">
          <div className="mb-12">
            <h1 className="text-3xl font-bold text-gray-900">Reddit Lead Generation</h1>
            <p className="text-gray-600 mt-2">
              AI-powered lead discovery from Reddit discussions
            </p>
          </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Step: Radars List */}
        {step === "campaigns" && (
          <div>
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Your Radars</h2>
              <button
                onClick={() => setStep("create")}
                className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
              >
                + New Radar
              </button>
            </div>

            {loading ? (
              <div className="text-center py-12">Loading radars...</div>
            ) : campaigns.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border">
                <p className="text-gray-500 mb-4">No radars yet</p>
                <button
                  onClick={() => setStep("create")}
                  className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
                >
                  Create Your First Radar
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {campaigns.map((campaign) => (
                  <div
                    key={campaign.id}
                    className="bg-white p-6 rounded-lg border hover:shadow-md transition"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-medium ${
                              campaign.status === "ACTIVE"
                                ? "bg-green-100 text-green-700"
                                : campaign.status === "DISCOVERING"
                                ? "bg-gray-800 text-white"
                                : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {campaign.status}
                          </span>
                        </div>
                        <p className="text-gray-900 font-medium mb-2">
                          {campaign.business_description}
                        </p>
                        <div className="flex gap-4 text-sm text-gray-600">
                          <span>{campaign.subreddits_count} subreddits</span>
                          <span>{campaign.leads_count} leads</span>
                          <span>
                            Polls every {campaign.poll_interval_hours}h
                          </span>
                          {campaign.last_poll_at && (
                            <span>
                              Last explored: {getTimeAgo(new Date(campaign.last_poll_at).getTime() / 1000)}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2 items-center">
                        <button
                          onClick={() => handleViewLeads(campaign)}
                          className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
                        >
                          View Leads
                        </button>
                        {/* Settings dropdown */}
                        <div className="relative">
                          <button
                            onClick={() => setOpenSettingsMenu(openSettingsMenu === campaign.id ? null : campaign.id)}
                            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                            title="Radar settings"
                          >
                            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-20">
                                {campaign.status === "ACTIVE" && (
                                  <button
                                    onClick={() => {
                                      handleRunNow(campaign);
                                      setOpenSettingsMenu(null);
                                    }}
                                    disabled={loading}
                                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-3 disabled:opacity-50"
                                  >
                                    <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                    Run Now
                                  </button>
                                )}
                                <button
                                  onClick={() => {
                                    handleToggleCampaign(campaign);
                                    setOpenSettingsMenu(null);
                                  }}
                                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-3"
                                >
                                  {campaign.status === "ACTIVE" ? (
                                    <>
                                      <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                      Pause
                                    </>
                                  ) : (
                                    <>
                                      <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                      Resume
                                    </>
                                  )}
                                </button>
                                <div className="border-t my-1"></div>
                                <button
                                  onClick={() => {
                                    handleDeleteCampaign(campaign);
                                    setOpenSettingsMenu(null);
                                  }}
                                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3"
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
                  </div>
                ))}
              </div>
            )}

            {/* How It Works Section */}
            <div className="mt-12 mb-12 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200 p-8 shadow-sm">
              <div className="flex items-center gap-3 mb-8">
                <div className="h-px bg-gradient-to-r from-gray-300 to-transparent flex-1"></div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">How It Works</h3>
                <div className="h-px bg-gradient-to-l from-gray-300 to-transparent flex-1"></div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
                {/* Arrow connector between steps - desktop only */}
                <div className="hidden md:block absolute top-12 left-1/3 right-1/3 h-px">
                  <div className="relative h-full">
                    <div className="absolute inset-0 flex items-center justify-between px-4">
                      <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                      <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Step 1 */}
                <div className="relative bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all group">
                  <div className="absolute -top-3 -left-3 w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <div className="pt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-bold text-blue-600 uppercase tracking-wide">Step 1</span>
                      <div className="h-px bg-blue-200 flex-1"></div>
                    </div>
                    <h4 className="text-base font-semibold text-gray-900 mb-2">Discover Communities</h4>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      Describe your business and our AI finds relevant subreddits where your potential customers are active.
                    </p>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="relative bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all group">
                  <div className="absolute -top-3 -left-3 w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="pt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-bold text-purple-600 uppercase tracking-wide">Step 2</span>
                      <div className="h-px bg-purple-200 flex-1"></div>
                    </div>
                    <h4 className="text-base font-semibold text-gray-900 mb-2">Track Posts</h4>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      We monitor discussions and identify high-intent posts from people looking for solutions like yours.
                    </p>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="relative bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all group">
                  <div className="absolute -top-3 -left-3 w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div className="pt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-bold text-green-600 uppercase tracking-wide">Step 3</span>
                      <div className="h-px bg-green-200 flex-1"></div>
                    </div>
                    <h4 className="text-base font-semibold text-gray-900 mb-2">Engage & Convert</h4>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      Review AI-generated responses and engage with potential customers at the perfect moment.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step: Create Radar */}
        {step === "create" && (
          <div className="bg-white p-8 rounded-lg border">
            <button
              onClick={() => setStep("campaigns")}
              className="text-gray-600 mb-6 hover:text-gray-900"
            >
              ← Back to Radars
            </button>

            <h2 className="text-2xl font-semibold mb-6">Create New Radar</h2>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Describe Your Business
              </label>
              <textarea
                value={businessDescription}
                onChange={(e) => setBusinessDescription(e.target.value)}
                className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                rows={4}
                placeholder="e.g., I sell project management SaaS for small teams"
              />
              <p className="text-sm text-gray-500 mt-2">
                Be specific about your product, target audience, and problems you solve
              </p>
            </div>

            <button
              onClick={handleCreateCampaign}
              disabled={loading}
              className="w-full px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
            >
              {loading ? "Creating Radar..." : "Create Radar & Discover Subreddits"}
            </button>
          </div>
        )}

        {/* Step: Discover & Select Subreddits */}
        {step === "discover" && (
          <div className="bg-white p-8 rounded-lg border">
            <h2 className="text-2xl font-semibold mb-6">
              Select Subreddits to Monitor
            </h2>

            {loading ? (
              <div className="text-center py-12">Discovering subreddits...</div>
            ) : (
              <>
                <div className="mb-6 flex items-center justify-between">
                  <p className="text-gray-600">
                    Selected: {selectedSubreddits.size} / {MAX_SUBREDDIT_SELECTION} subreddits
                    {selectedSubreddits.size >= MAX_SUBREDDIT_SELECTION && (
                      <span className="text-amber-600 ml-2">(max reached)</span>
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

        {/* Step: View Leads - Inbox Style */}
        {step === "leads" && currentCampaign && (
          <div className="fixed top-16 left-0 right-0 bottom-0 bg-white flex">
            {/* Left Sidebar - Subreddit Filters */}
            <div className="w-64 border-r bg-gray-50 overflow-y-auto">
              <div className="pt-8 px-6 pb-6">
                <button
                  onClick={() => {
                    setStep("campaigns");
                    setLeads([]);
                    setSelectedLead(null);
                  }}
                  className="text-gray-600 mb-8 hover:text-gray-900 text-sm flex items-center gap-1"
                >
                  <span>←</span> Back to Radars
                </button>

                <h2 className="text-xl font-bold mb-6">Inbox</h2>

                {/* Status Tabs */}
                <div className="mb-6">
                  <div className="space-y-1">
                    {["Inbox", "Commented", "DMed"].map((tab, idx) => {
                      const statusMap: Record<string, string> = {
                        "Inbox": "NEW",
                        "Commented": "REVIEWED",
                        "DMed": "CONTACTED"
                      };
                      const countMap: Record<string, number> = {
                        "Inbox": leadCounts.new,
                        "Commented": leadCounts.reviewed,
                        "DMed": leadCounts.contacted
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
                          className={`w-full text-left px-3 py-2 rounded text-sm flex justify-between items-center ${
                            filterStatus === status
                              ? "bg-gray-200 font-medium"
                              : "hover:bg-gray-100"
                          }`}
                        >
                          <span>{tab}</span>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
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
                  <div className="flex items-center justify-between mb-2 px-3">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase">
                      Filter by Subreddit
                    </h3>
                    <button
                      onClick={handleOpenAddSubreddit}
                      className="text-gray-900 hover:text-gray-700"
                      title="Add Subreddit"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                      </svg>
                    </button>
                  </div>
                  <button
                    onClick={() => setSelectedSubreddit("all")}
                    className={`w-full text-left px-3 py-2 rounded text-sm flex justify-between items-center ${
                      selectedSubreddit === "all"
                        ? "bg-gray-200 font-medium"
                        : "hover:bg-gray-100"
                    }`}
                  >
                    <span>All subreddits</span>
                    <span className="text-xs text-gray-500">{leads.length}</span>
                  </button>
                  
                  {Array.from(new Set(leads.map(l => l.subreddit_name))).map((subreddit) => {
                    const count = leads.filter(l => l.subreddit_name === subreddit).length;
                    return (
                      <button
                        key={subreddit}
                        onClick={() => setSelectedSubreddit(subreddit)}
                        className={`w-full text-left px-3 py-2 rounded text-sm flex justify-between items-center ${
                          selectedSubreddit === subreddit
                            ? "bg-gray-200 font-medium"
                            : "hover:bg-gray-100"
                        }`}
                      >
                        <span>r/{subreddit}</span>
                        <span className="text-xs text-gray-500">{count}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Center - Leads List */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Header */}
              <div className="border-b px-6 pt-8 pb-4 flex items-center justify-between bg-white">
                <div className="flex items-center gap-4">
                  {/* Overall Relevancy Badge */}
                  <div className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg border border-green-200">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-semibold">
                      {leads.length > 0 ? Math.round(leads.reduce((acc, l) => {
                        const score = l.relevancy_score || 0;
                        // Support both old (0.0-1.0) and new (0-100) formats
                        return acc + (score <= 1 ? score * 100 : score);
                      }, 0) / leads.length) : 0}%
                    </span>
                    <span className="text-xs text-green-600">Overall relevancy</span>
                  </div>
                  
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

                  {/* Run Now Button */}
                  {currentCampaign && currentCampaign.status === "ACTIVE" && (
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
                  <div className="text-center py-12 text-gray-500">Loading leads...</div>
                ) : leads.filter(l => selectedSubreddit === "all" || l.subreddit_name === selectedSubreddit).length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-500">No leads found</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Try changing filters or wait for the next polling cycle
                    </p>
                    {currentCampaign && currentCampaign.status === "ACTIVE" && (
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
                  <div className="divide-y">
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
                        return (
                          <div
                            key={lead.id}
                            onClick={() => setSelectedLead(lead)}
                            className={`px-6 py-4 cursor-pointer transition ${
                              selectedLead?.id === lead.id
                                ? "bg-gray-50 border-l-4 border-gray-900"
                                : "hover:bg-gray-50"
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <div className="flex items-center gap-2 px-2 py-1 bg-green-50 text-green-700 rounded text-xs font-medium">
                                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                                {relevancyPercent}%
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                                  <span>u/{lead.author || '[deleted]'}</span>
                                  <span>•</span>
                                  <span>r/{lead.subreddit_name || 'unknown'}</span>
                                  <span>•</span>
                                  <span>{timeAgo}</span>
                                </div>
                                <h3 className="font-semibold text-gray-900 mb-1 truncate">
                                  {lead.title || 'Untitled'}
                                </h3>
                                <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                                  {lead.content ? (lead.content.substring(0, 150) + (lead.content.length > 150 ? '...' : '')) : 'No content'}
                                </p>
                                <div className="flex items-center gap-3 text-xs text-gray-500">
                                  <span className="flex items-center gap-1">
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                                    </svg>
                                    {lead.score || 0}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                    </svg>
                                    {lead.num_comments || 0}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            </div>

            {/* Right Panel - Lead Details */}
            {selectedLead && (
              <div 
                className="border-l bg-white overflow-y-auto relative"
                style={{ width: `${detailPanelWidth}px` }}
              >
                {/* Resize Handle */}
                <div
                  className={`absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-900 transition-colors ${
                    isResizing ? 'bg-gray-900' : 'bg-transparent'
                  }`}
                  onMouseDown={handleMouseDown}
                  style={{ zIndex: 10 }}
                >
                  <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 rounded-full" />
                </div>
                <div className="p-8">
                  {/* Header */}
                  <div className="mb-6">
                    <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                      <span>u/{selectedLead.author || '[deleted]'}</span>
                      <span>•</span>
                      <span>r/{selectedLead.subreddit_name || 'unknown'}</span>
                      <span>•</span>
                      <span>{getTimeAgo(selectedLead.created_utc || 0)}</span>
                    </div>
                    <h2 className="text-xl font-bold mb-4">{selectedLead.title || 'Untitled'}</h2>
                    <p className="text-sm text-gray-700 mb-4 whitespace-pre-wrap">
                      {selectedLead.content || 'No content available'}
                    </p>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                        </svg>
                        {selectedLead.score || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        {selectedLead.num_comments || 0}
                      </span>
                    </div>
                  </div>

                  {/* Reasoning */}
                  <div className="mb-6">
                    <button className="flex items-center gap-2 text-sm font-medium mb-2 text-gray-700">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Reasoning
                    </button>
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                      {selectedLead.relevancy_reason || 'No reasoning available'}
                    </p>
                  </div>

                  {/* Suggested Comment */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <button className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                        </svg>
                        Suggested comment
                      </button>
                      <button className="text-xs text-gray-500 flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Comment prompt
                      </button>
                    </div>
                    <p className="text-sm text-gray-700 bg-amber-50 p-3 rounded mb-2">
                      {selectedLead.suggested_comment || 'No suggested comment available'}
                    </p>
                    <button 
                      onClick={() => handleCopyAndComment(selectedLead)}
                      className="w-full px-4 py-2 bg-gray-900 text-white rounded text-sm hover:bg-gray-800 flex items-center justify-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy & comment manually
                    </button>
                  </div>

                  {/* Suggested DM */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <button className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                        Suggested DM
                      </button>
                      <button className="text-xs text-gray-500 flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        DM prompt
                      </button>
                    </div>
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded mb-2">
                      {selectedLead.suggested_dm || 'No suggested DM available'}
                    </p>
                    <button 
                      onClick={() => handleCopyAndDM(selectedLead)}
                      className="w-full px-4 py-2 bg-gray-900 text-white rounded text-sm hover:bg-gray-800 flex items-center justify-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy & DM manually
                    </button>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <a
                      href={selectedLead.post_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 px-4 py-2 border rounded text-sm hover:bg-gray-50 text-center"
                    >
                      View on Reddit
                    </a>
                    <Dropdown
                      options={[
                        { value: "NEW", label: "New" },
                        { value: "REVIEWED", label: "Reviewed" },
                        { value: "CONTACTED", label: "Contacted" },
                        { value: "DISMISSED", label: "Dismissed" },
                      ]}
                      value={selectedLead.status}
                      onChange={(value) => handleUpdateStatus(selectedLead.id, value)}
                      className="text-sm"
                    />
                  </div>
                </div>
              </div>
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
                    {loadingSubreddits ? (
                      <div className="text-center py-8 text-gray-500">Loading...</div>
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
                    {loadingSubreddits ? (
                      <div className="text-center py-8 text-gray-500">Loading recommendations...</div>
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
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Radar Activated</h3>
              <p className="text-sm text-gray-600 mb-6">
                Leads will appear after the polling cycle (every 6 hours).
              </p>
              <button
                onClick={() => {
                  setShowSuccessDialog(false);
                  setStep("campaigns");
                  setSelectedSubreddits(new Map());
                }}
                className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}

