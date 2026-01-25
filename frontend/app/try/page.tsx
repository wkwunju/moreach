"use client";

import { useEffect, useMemo, useState } from "react";
import { createRequest, fetchResults } from "../../lib/api";
import type { InfluencerResponse, RequestStatus } from "../../lib/types";
import Navigation from "../../components/Navigation";

const STATUS_COPY: Record<RequestStatus, string> = {
  PARTIAL: "Partial results from the existing index.",
  PROCESSING: "Discovery in progress. Pulling new creators.",
  DONE: "Discovery complete. Ranked results below.",
  FAILED: "We hit an error. Try again or refine your query."
};

export default function TryPage() {
  const [description, setDescription] = useState("");
  const [constraints, setConstraints] = useState("");
  const [requestId, setRequestId] = useState<number | null>(null);
  const [status, setStatus] = useState<RequestStatus | null>(null);
  const [results, setResults] = useState<InfluencerResponse[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!requestId) {
      return;
    }

    let isActive = true;

    const poll = async () => {
      try {
        const payload = await fetchResults(requestId);
        if (!isActive) {
          return;
        }
        setStatus(payload.status);
        setResults(payload.results);
      } catch (err) {
        if (!isActive) {
          return;
        }
        setError("Unable to load results. Please retry.");
      }
    };

    poll();
    const interval = setInterval(poll, 5000);

    return () => {
      isActive = false;
      clearInterval(interval);
    };
  }, [requestId]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResults([]);

    try {
      const response = await createRequest(description, constraints);
      setRequestId(response.id);
      setStatus(response.status);
    } catch (err) {
      setError("We could not start discovery. Check the API and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const statusBadge = useMemo(() => {
    if (!status) {
      return null;
    }

    const styleMap: Record<RequestStatus, string> = {
      PARTIAL: "bg-orange-100 text-orange-700",
      PROCESSING: "bg-blue-100 text-blue-700",
      DONE: "bg-green-100 text-green-700",
      FAILED: "bg-red-100 text-red-700"
    };

    return (
      <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${styleMap[status]}`}>
        {status}
      </span>
    );
  }, [status]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <main className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Try Influencer Discovery
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Describe your business and constraints. Our AI will find the perfect creators for you.
            </p>
          </div>

          {/* Main Content */}
          <div className="grid lg:grid-cols-[1fr_1.5fr] gap-8">
            {/* Search Form */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Business Description
                  </label>
                  <textarea
                    required
                    rows={5}
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    placeholder="We sell premium hydration mixes for endurance athletes..."
                    className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Constraints
                  </label>
                  <textarea
                    rows={4}
                    value={constraints}
                    onChange={(event) => setConstraints(event.target.value)}
                    placeholder="US-based, 25-40, fitness + trail running, 20k-200k followers"
                    className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-xl bg-gray-900 px-6 py-3.5 text-sm font-semibold uppercase tracking-wider text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-400"
                >
                  {isSubmitting ? "Launching..." : "Launch Discovery"}
                </button>
                
                {error && (
                  <p className="text-sm text-red-600">{error}</p>
                )}
              </form>

              {/* Status Panel */}
              <div className="mt-8 pt-8 border-t border-gray-200">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-900">
                    Status
                  </h3>
                  {statusBadge}
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  {status ? STATUS_COPY[status] : "Submit a request to start discovery."}
                </p>
                <div className="space-y-2 text-xs text-gray-500">
                  <p>Pipeline: intent → embed → vector search → async enrichment</p>
                  <p className="animate-pulse">Refreshes every 5 seconds</p>
                </div>
              </div>
            </div>

            {/* Results Panel */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-900">
                  Ranked Creators
                </h2>
                <span className="text-xs text-gray-500">{results.length} matches</span>
              </div>
              
              <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2">
                {results.length === 0 ? (
                  <div className="rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
                    <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <p className="text-sm text-gray-500">
                      Results will populate here once vector search returns matches.
                    </p>
                  </div>
                ) : (
                  results.map((creator) => (
                    <ResultCard key={creator.id} creator={creator} />
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ResultCard({ creator }: { creator: InfluencerResponse }) {
  const number = new Intl.NumberFormat("en-US");
  const [expanded, setExpanded] = useState(false);
  
  // Calculate engagement rate
  const engagementRate = creator.followers > 0 
    ? ((creator.avg_likes + creator.avg_comments) / creator.followers * 100).toFixed(2)
    : '0.00';
  
  // Calculate match score percentage
  const matchScore = (creator.score * 100).toFixed(1);
  
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 hover:shadow-md transition">
      {/* Header with Match Score Badge */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-base font-semibold text-gray-900">@{creator.handle}</p>
            {creator.country && (
              <span className="text-xs text-gray-500">📍 {creator.country}</span>
            )}
            <span className="ml-auto px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
              {matchScore}% match
            </span>
          </div>
          <p className="text-sm text-gray-600">{creator.name || "Creator"}</p>
        </div>
        <div className="flex gap-2">
          {creator.email && (
            <a
              href={`mailto:${creator.email}`}
              className="text-xs font-semibold uppercase tracking-wider text-blue-600 hover:text-blue-800"
              title="Email"
            >
              ✉
            </a>
          )}
          {creator.external_url && (
            <a
              href={creator.external_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs font-semibold uppercase tracking-wider text-purple-600 hover:text-purple-800"
              title="External Link"
            >
              🔗
            </a>
          )}
          <a
            href={creator.profile_url}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1 bg-gray-900 text-white text-xs font-semibold rounded-lg hover:bg-gray-800"
          >
            View Profile
          </a>
        </div>
      </div>
      
      {/* Category and Engagement Badge */}
      <div className="flex items-center gap-2 mb-3">
        {creator.category && (
          <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full">
            {creator.category}
          </span>
        )}
        <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
          {engagementRate}% engagement
        </span>
      </div>
      
      <p className="text-sm text-gray-700 mb-4">
        {creator.profile_summary || creator.bio || "No bio available."}
      </p>
      
      {/* Basic Metrics */}
      <div className="grid grid-cols-4 gap-4 text-sm mb-4">
        <div>
          <p className="text-xs text-gray-500 mb-1">Followers</p>
          <p className="font-semibold text-gray-900">{number.format(creator.followers)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Avg Likes</p>
          <p className="font-semibold text-gray-900">{number.format(creator.avg_likes)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Avg Comments</p>
          <p className="font-semibold text-gray-900">{number.format(creator.avg_comments)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Avg Views</p>
          <p className="font-semibold text-gray-900">
            {creator.avg_video_views > 0 ? number.format(creator.avg_video_views) : 'N/A'}
          </p>
        </div>
      </div>
      
      {/* Expandable Details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-xs font-semibold uppercase tracking-wider text-blue-600 hover:text-blue-800 transition"
      >
        {expanded ? "▼ Hide Details" : "▶ Show Details"}
      </button>
      
      {expanded && (
        <div className="mt-4 space-y-4 border-t border-gray-200 pt-4">
          {/* Peak Performance */}
          {(creator.highest_likes > 0 || creator.highest_comments > 0 || creator.highest_video_views > 0) && (
            <div>
              <p className="text-xs uppercase tracking-wider text-orange-600 font-semibold mb-2">
                Peak Performance
              </p>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-xs text-gray-500">Highest Likes</p>
                  <p className="font-semibold text-gray-900">{number.format(creator.highest_likes)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Highest Comments</p>
                  <p className="font-semibold text-gray-900">{number.format(creator.highest_comments)}</p>
                </div>
                {creator.highest_video_views > 0 && (
                  <div>
                    <p className="text-xs text-gray-500">Highest Views</p>
                    <p className="font-semibold text-gray-900">{number.format(creator.highest_video_views)}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Content Analysis */}
          {(creator.post_sharing_percentage > 0 || creator.post_collaboration_percentage > 0) && (
            <div>
              <p className="text-xs uppercase tracking-wider text-purple-600 font-semibold mb-2">
                Content Analysis
              </p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-xs text-gray-500">Sharing Posts</p>
                  <p className="font-semibold text-gray-900">{creator.post_sharing_percentage.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Collaborations</p>
                  <p className="font-semibold text-gray-900">{creator.post_collaboration_percentage.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          )}
          
          {/* Audience Analysis */}
          {creator.audience_analysis && (
            <div>
              <p className="text-xs uppercase tracking-wider text-green-600 font-semibold mb-2">
                Audience Profile
              </p>
              <p className="text-sm text-gray-700">{creator.audience_analysis}</p>
            </div>
          )}
          
          {/* Collaboration Opportunity */}
          {creator.collaboration_opportunity && (
            <div>
              <p className="text-xs uppercase tracking-wider text-blue-600 font-semibold mb-2">
                Collaboration Potential
              </p>
              <p className="text-sm text-gray-700">{creator.collaboration_opportunity}</p>
            </div>
          )}
        </div>
      )}
      
      {/* Tags */}
      <div className="mt-4 flex flex-wrap gap-2">
        {creator.category && (
          <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
            {creator.category}
          </span>
        )}
        {creator.gender && (
          <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
            {creator.gender}
          </span>
        )}
        {creator.tags && (
          <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
            {creator.tags}
          </span>
        )}
      </div>
    </div>
  );
}

