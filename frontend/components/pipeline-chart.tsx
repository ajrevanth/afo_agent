"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { DashboardStats } from "@/lib/types";
import { STATE_LABELS } from "@/lib/utils";

interface Props {
  stats: DashboardStats | null;
  loading: boolean;
}

const COLORS: Record<string, string> = {
  received: "#94a3b8",
  processing: "#60a5fa",
  classified: "#a78bfa",
  extracted: "#fbbf24",
  completed: "#34d399",
  failed: "#f87171",
};

export function PipelineChart({ stats, loading }: Props) {
  const data = stats
    ? Object.entries(stats.by_state).map(([state, count]) => ({
        state: STATE_LABELS[state as keyof typeof STATE_LABELS] ?? state,
        key: state,
        count,
      }))
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Pipeline State Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-48 animate-pulse rounded bg-muted" />
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="state" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {data.map((entry) => (
                  <Cell key={entry.key} fill={COLORS[entry.key] ?? "#94a3b8"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
