import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TypeBadge, StatusBadge } from "@/components/status-badge";
import { RefreshCw, ArrowRight, AlertTriangle, Clock } from "lucide-react";
import { formatCurrency, isUrgent, daysUntil } from "@/lib/utils";
import type { Document } from "@/lib/types";

interface Props {
  documents: Document[];
  loading: boolean;
  onRefresh: () => void;
}

export function UrgentQueue({ documents, loading, onRefresh }: Props) {
  const capitalCalls = documents.filter((d) => d.document_type === "capital_call");
  const other = documents.filter((d) => d.document_type !== "capital_call");
  const sorted = [
    ...capitalCalls.sort((a, b) => {
      const da = a.metadata?.due_date ? daysUntil(a.metadata.due_date) : 999;
      const db = b.metadata?.due_date ? daysUntil(b.metadata.due_date) : 999;
      return da - db;
    }),
    ...other,
  ];

  const hasUrgent = sorted.some((d) => isUrgent(d.metadata?.due_date));

  return (
    <Card className={hasUrgent ? "border-orange-200" : undefined}>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          {hasUrgent && <AlertTriangle className="h-4 w-4 text-orange-500" />}
          Pending Review
          {!loading && sorted.length > 0 && (
            <span className="ml-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-orange-100 px-1.5 text-xs font-bold text-orange-800">
              {sorted.length}
            </span>
          )}
        </CardTitle>
        <Button variant="ghost" size="icon" onClick={onRefresh} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />)}
          </div>
        ) : sorted.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <div className="rounded-full bg-green-50 p-3">
              <Clock className="h-5 w-5 text-green-600" />
            </div>
            <p className="text-sm font-medium text-green-700">All clear — no documents pending review</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sorted.map((doc) => {
              const urgent = isUrgent(doc.metadata?.due_date);
              const days = doc.metadata?.due_date ? daysUntil(doc.metadata.due_date) : null;

              return (
                <Link
                  key={doc.id}
                  href={`/documents/${doc.id}`}
                  className={`flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-muted/40 ${
                    urgent ? "border-orange-200 bg-orange-50/50" : ""
                  }`}
                >
                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      {doc.document_type && doc.document_type !== "unknown" && <TypeBadge type={doc.document_type} />}
                      {urgent && (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700">
                          {days === 0 ? "DUE TODAY" : days === 1 ? "DUE TOMORROW" : days !== null && days < 0 ? "OVERDUE" : `${days}d left`}
                        </span>
                      )}
                    </div>
                    <p className="truncate text-sm font-medium">{doc.filename}</p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {doc.metadata?.fund_name && <span>{doc.metadata.fund_name}</span>}
                      {doc.metadata?.amount && (
                        <span className="font-semibold text-foreground">
                          {formatCurrency(doc.metadata.amount, doc.metadata.currency)}
                        </span>
                      )}
                      {doc.metadata?.due_date && <span>Due: {doc.metadata.due_date}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge state={doc.state} />
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
