import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { formatDate } from "@/lib/utils";
import type { Document } from "@/lib/types";

interface Props {
  documents: Document[];
  loading: boolean;
}

export function ActivityFeed({ documents, loading }: Props) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-base">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded bg-muted" />
          ))
        ) : documents.length === 0 ? (
          <p className="text-sm text-muted-foreground">No documents yet.</p>
        ) : (
          documents.map((doc) => (
            <Link
              key={doc.id}
              href={`/documents/${doc.id}`}
              className="flex items-start gap-3 rounded-md border-b pb-2 last:border-0 last:pb-0 hover:bg-muted/30 px-1 py-1 transition-colors"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{doc.filename}</p>
                <p className="text-xs text-muted-foreground">{formatDate(doc.updated_at)}</p>
              </div>
              <StatusBadge state={doc.state} />
            </Link>
          ))
        )}
      </CardContent>
    </Card>
  );
}
