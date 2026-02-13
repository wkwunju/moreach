"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUser, authFetch } from "@/lib/auth";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const ADMIN_EMAIL = "wkwunju@gmail.com";

interface DashboardData {
  generated_at: string;
  overview: {
    total_users: number;
    active_users_7d: number;
    new_users_7d: number;
    new_users_30d: number;
    total_campaigns: number;
    active_campaigns: number;
    total_leads: number;
    contacted_leads: number;
    contact_rate: number;
  };
  user_growth: { date: string; count: number }[];
  retention: {
    active_24h: number;
    active_1_7d: number;
    active_7_30d: number;
    active_30d_plus: number;
    never_logged_in: number;
  };
  api_usage: {
    date: string;
    api_type: string;
    calls: number;
    input_tokens: number;
    output_tokens: number;
  }[];
  llm_costs: {
    api_type: string;
    calls: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost_usd: number;
  }[];
  per_user: {
    id: number;
    email: string;
    full_name: string;
    subscription_tier: string;
    created_at: string | null;
    last_login_at: string | null;
    campaigns: number;
    leads: number;
    contacted: number;
    contact_rate: number;
    api_calls: number;
  }[];
  campaign_health: {
    total_polls_7d: number;
    successful: number;
    failed: number;
    success_rate: number;
    avg_leads_per_poll: number;
  };
}

type SortKey = keyof DashboardData["per_user"][0];

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function AdminDashboard() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortAsc, setSortAsc] = useState(false);

  // Client-side guard
  useEffect(() => {
    const user = getUser();
    if (!user || user.email !== ADMIN_EMAIL) {
      router.replace("/");
      return;
    }
  }, [router]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`${baseUrl}/api/v1/admin/dashboard`);
      if (!res.ok) {
        if (res.status === 404) {
          router.replace("/");
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const user = getUser();
    if (user?.email === ADMIN_EMAIL) {
      fetchData();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button onClick={fetchData} className="px-4 py-2 bg-gray-900 text-white rounded-lg">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { overview, retention, campaign_health, llm_costs, user_growth, api_usage, per_user } = data;

  // Growth chart
  const maxGrowth = Math.max(...user_growth.map((r) => r.count), 1);

  // Retention total
  const retTotal =
    retention.active_24h +
    retention.active_1_7d +
    retention.active_7_30d +
    retention.active_30d_plus +
    retention.never_logged_in;

  // Sorted per-user table
  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  const sortedUsers = [...per_user].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (aVal == null && bVal == null) return 0;
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortAsc ? Number(aVal) - Number(bVal) : Number(bVal) - Number(aVal);
  });

  const retentionBuckets = [
    { label: "Active 24h", value: retention.active_24h, color: "bg-green-500" },
    { label: "1-7 days", value: retention.active_1_7d, color: "bg-green-300" },
    { label: "7-30 days", value: retention.active_7_30d, color: "bg-yellow-400" },
    { label: "30+ days", value: retention.active_30d_plus, color: "bg-orange-400" },
    { label: "Never", value: retention.never_logged_in, color: "bg-gray-300" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Generated at {new Date(data.generated_at).toLocaleString()}
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800"
        >
          Refresh
        </button>
      </div>

      {/* Overview Cards */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Users" value={overview.total_users} />
          <StatCard label="Active (7d)" value={overview.active_users_7d} />
          <StatCard label="New (7d)" value={overview.new_users_7d} />
          <StatCard label="New (30d)" value={overview.new_users_30d} />
          <StatCard label="Total Campaigns" value={overview.total_campaigns} />
          <StatCard label="Active Campaigns" value={overview.active_campaigns} />
          <StatCard label="Total Leads" value={overview.total_leads} />
          <StatCard label="Contact Rate" value={`${overview.contact_rate}%`} />
        </div>
      </section>

      {/* User Growth */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">User Growth (30 days)</h2>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-end gap-1 h-40">
            {user_growth.map((day) => (
              <div key={day.date} className="flex-1 flex flex-col items-center justify-end h-full">
                <div
                  className="w-full bg-blue-500 rounded-t min-h-[2px]"
                  style={{ height: `${(day.count / maxGrowth) * 100}%` }}
                  title={`${day.date}: ${day.count} users`}
                />
              </div>
            ))}
          </div>
          {user_growth.length > 0 && (
            <div className="flex justify-between text-xs text-gray-400 mt-2">
              <span>{user_growth[0].date}</span>
              <span>{user_growth[user_growth.length - 1].date}</span>
            </div>
          )}
        </div>
      </section>

      {/* Retention */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Retention</h2>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex rounded-full overflow-hidden h-8 mb-4">
            {retentionBuckets.map((b) =>
              b.value > 0 ? (
                <div
                  key={b.label}
                  className={`${b.color} relative`}
                  style={{ width: `${(b.value / retTotal) * 100}%` }}
                  title={`${b.label}: ${b.value}`}
                />
              ) : null
            )}
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            {retentionBuckets.map((b) => (
              <div key={b.label} className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${b.color}`} />
                <span className="text-gray-600">
                  {b.label}: {b.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* LLM Costs */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">LLM Costs</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {llm_costs.map((c) => (
            <div key={c.api_type} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="font-medium text-gray-900 mb-2">{c.api_type}</div>
              <div className="text-2xl font-bold text-green-600">${c.estimated_cost_usd}</div>
              <div className="text-sm text-gray-500 mt-2 space-y-1">
                <div>Calls: {c.calls.toLocaleString()}</div>
                <div>Input: {c.input_tokens.toLocaleString()} tokens</div>
                <div>Output: {c.output_tokens.toLocaleString()} tokens</div>
              </div>
            </div>
          ))}
          {llm_costs.length === 0 && (
            <div className="text-gray-500 text-sm">No LLM usage data yet.</div>
          )}
        </div>
      </section>

      {/* API Usage */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">API Usage (30 days)</h2>
        <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                <th className="p-3">Date</th>
                <th className="p-3">API Type</th>
                <th className="p-3 text-right">Calls</th>
                <th className="p-3 text-right">Input Tokens</th>
                <th className="p-3 text-right">Output Tokens</th>
              </tr>
            </thead>
            <tbody>
              {api_usage.map((r, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="p-3">{r.date}</td>
                  <td className="p-3">{r.api_type}</td>
                  <td className="p-3 text-right">{r.calls.toLocaleString()}</td>
                  <td className="p-3 text-right">{r.input_tokens.toLocaleString()}</td>
                  <td className="p-3 text-right">{r.output_tokens.toLocaleString()}</td>
                </tr>
              ))}
              {api_usage.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-3 text-center text-gray-500">
                    No API usage data yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Per-User Table */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Per-User Breakdown</h2>
        <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                {(
                  [
                    ["email", "Email"],
                    ["subscription_tier", "Plan"],
                    ["created_at", "Joined"],
                    ["last_login_at", "Last Login"],
                    ["campaigns", "Campaigns"],
                    ["leads", "Leads"],
                    ["contacted", "Contacted"],
                    ["contact_rate", "Contact %"],
                    ["api_calls", "API Calls"],
                  ] as [SortKey, string][]
                ).map(([key, label]) => (
                  <th
                    key={key}
                    className="p-3 cursor-pointer hover:text-gray-900 select-none whitespace-nowrap"
                    onClick={() => handleSort(key)}
                  >
                    {label}
                    {sortKey === key && (sortAsc ? " ↑" : " ↓")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedUsers.map((u) => (
                <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-3 whitespace-nowrap">{u.email}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700">
                      {u.subscription_tier}
                    </span>
                  </td>
                  <td className="p-3 whitespace-nowrap">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : "-"}
                  </td>
                  <td className="p-3 whitespace-nowrap">
                    {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "Never"}
                  </td>
                  <td className="p-3 text-right">{u.campaigns}</td>
                  <td className="p-3 text-right">{u.leads}</td>
                  <td className="p-3 text-right">{u.contacted}</td>
                  <td className="p-3 text-right">{u.contact_rate}%</td>
                  <td className="p-3 text-right">{u.api_calls.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Campaign Health */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Campaign Health (7 days)</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Polls" value={campaign_health.total_polls_7d} />
          <StatCard label="Successful" value={campaign_health.successful} />
          <StatCard label="Failed" value={campaign_health.failed} />
          <StatCard label="Success Rate" value={`${campaign_health.success_rate}%`} />
          <StatCard label="Avg Leads/Poll" value={campaign_health.avg_leads_per_poll} />
        </div>
      </section>
    </div>
  );
}
