import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react";
import type { DashboardStats } from "@/lib/types";

interface Props {
  stats: DashboardStats | null;
  loading: boolean;
}

export function StatsCards({ stats, loading }: Props) {
  const cards = [
    {
      title: "Total Documents",
      value: stats?.total ?? 0,
      icon: FileText,
      color: "text-blue-600",
      bg: "bg-blue-50",
      sub: null,
    },
    {
      title: "Pending Review",
      value: stats?.pending_review_count ?? 0,
      icon: Clock,
      color: "text-orange-600",
      bg: "bg-orange-50",
      sub: stats?.urgent_count
        ? `${stats.urgent_count} urgent`
        : null,
      highlight: (stats?.pending_review_count ?? 0) > 0,
    },
    {
      title: "Approved Today",
      value: stats?.completed_today ?? 0,
      icon: CheckCircle,
      color: "text-green-600",
      bg: "bg-green-50",
      sub: null,
    },
    {
      title: "Failed / Attention",
      value: (stats?.by_state?.failed ?? 0) + (stats?.by_state?.needs_attention ?? 0),
      icon: AlertTriangle,
      color: "text-red-600",
      bg: "bg-red-50",
      sub: null,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {cards.map(({ title, value, icon: Icon, color, bg, sub, highlight }) => (
        <Card key={title} className={highlight ? "border-orange-200 bg-orange-50/40" : undefined}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
            <div className={`rounded-full p-2 ${bg}`}>
              <Icon className={`h-4 w-4 ${color}`} />
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-8 w-16 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <p className={`text-2xl font-bold ${highlight && value > 0 ? "text-orange-700" : ""}`}>
                  {value}
                </p>
                {sub && <p className="text-xs font-medium text-red-600 mt-0.5">{sub}</p>}
              </>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
