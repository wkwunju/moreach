export type RequestStatus = "PARTIAL" | "PROCESSING" | "DONE" | "FAILED";

export interface RequestResponse {
  id: number;
  status: RequestStatus;
  created_at: string;
}

export interface InfluencerResponse {
  id: number;
  handle: string;
  name: string;
  bio: string;
  profile_summary: string;
  category: string;
  tags: string;
  
  // Basic metrics
  followers: number;
  avg_likes: number;
  avg_comments: number;
  avg_video_views: number;
  
  // Peak performance metrics
  highest_likes: number;
  highest_comments: number;
  highest_video_views: number;
  
  // Post analysis metrics
  post_sharing_percentage: number;
  post_collaboration_percentage: number;
  
  // Advanced analysis
  audience_analysis: string;
  collaboration_opportunity: string;
  
  // Contact information
  email: string;
  external_url: string;
  
  // Location and demographics
  country: string;
  gender: string;
  
  profile_url: string;
  score: number;
  rank: number;
}

export interface ResultsResponse {
  request_id: number;
  status: RequestStatus;
  results: InfluencerResponse[];
}

// ======= Reddit Types =======

export type RedditCampaignStatus = "DISCOVERING" | "ACTIVE" | "PAUSED" | "COMPLETED" | "DELETED";
export type RedditLeadStatus = "NEW" | "CONTACTED" | "DISMISSED";

export interface RedditCampaign {
  id: number;
  status: RedditCampaignStatus;
  business_description: string;
  search_queries: string;
  poll_interval_hours: number;
  last_poll_at: string | null;
  created_at: string;
  subreddits_count: number;
  leads_count: number;
}

export interface SubredditInfo {
  name: string;
  title: string;
  description: string;
  subscribers: number;
  url: string;
  relevance_score?: number;
}

export interface SubredditRule {
  short_name: string;
  description: string;
  kind: string;
  priority: number;
}

export interface SubredditRulesResponse {
  subreddit_name: string;
  rules: SubredditRule[];
  rules_summary: string;
}

export interface RedditLead {
  id: number;
  reddit_post_id: string;
  subreddit_name: string;
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
  status: RedditLeadStatus;
  discovered_at: string;
  // Lazy suggestion generation tracking
  has_suggestions?: boolean;
  suggestions_generated_at?: string;
}

export interface RedditLeadsResponse {
  campaign_id: number;
  total_leads: number;
  new_leads: number;
  contacted_leads: number;
  leads: RedditLead[];
}
