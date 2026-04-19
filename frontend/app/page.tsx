"use client";

import { useEffect, useState } from "react";
import { StatsCards } from "@/components/stats-cards";
import { UrgentQueue } from "@/components/urgent-queue";
import { PipelineChart } from "@/components/pipeline-chart";
import { ActivityFeed } from "@/components/activity-feed";
import { fetchDashboardStats, fetchDocuments } from "@/lib/api";
import type { DashboardStats, Document } from "@/lib/types";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pending, setPending] = useState<Document[]>([]);
  const [recent, setRecent] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [s, p, r] = await Promise.all([
        fetchDashboardStats(),
        fetchDocuments({ state: "pending_review" }),
        fetchDocuments({}),
      ]);
      setStats(s);
      setPending(p);
      setRecent(r.slice(0, 8));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Operations Dashboard</h1>
          <p className="text-muted-foreground">Automated Fund Operations — Human Review Queue</p>
        </div>
        {stats && stats.pending_review_count > 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-orange-50 border border-orange-200 px-4 py-2">
            <span className="h-2.5 w-2.5 rounded-full bg-orange-500 animate-pulse" />
            <span className="text-sm font-semibold text-orange-800">
              {stats.pending_review_count} document{stats.pending_review_count !== 1 ? "s" : ""} awaiting review
            </span>
          </div>
        )}
      </div>

      <StatsCards stats={stats} loading={loading} />

      <UrgentQueue documents={pending} loading={loading} onRefresh={load} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <PipelineChart stats={stats} loading={loading} />
        </div>
        <div>
          <ActivityFeed documents={recent} loading={loading} />
        </div>
      </div>
    </div>
  );
}
